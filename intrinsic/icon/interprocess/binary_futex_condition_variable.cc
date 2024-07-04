// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/binary_futex_condition_variable.h"

#include "absl/base/thread_annotations.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/lockable_binary_futex.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"

namespace intrinsic::icon {

RealtimeStatus BinaryFutexConditionVariable::Await(LockableBinaryFutex *mutex,
                                                   absl::Condition condition,
                                                   absl::Time deadline)
    ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex) {
  CHECK(mutex != nullptr);
  // Assert again in case the compile time macros did not work.
  if (!mutex->IsHeld()) {
    return RealtimeStatus(absl::StatusCode::kFailedPrecondition,
                          "Mutex is not held when calling Await().");
  }
  // Check condition immediately.
  while (!condition.Eval()) {
    // Unlock before starting to wait so that another thread can acquire the
    // mutex to change the condition data.
    if (auto status = mutex->Unlock(); !status.ok()) {
      // We need to lock on every exit path.
      (void)(mutex->Lock());
      return status;
    }

    // Wait until woken up by the notify thread (the thread which calls
    // `NotifyOne()`) or reaching the deadline.
    // It does not matter if the notify thread calls `NotifyOne()` between the
    // `Unlock()` and `WaitUntil()`, since `BinaryFutex::WaitUntil()` gives the
    // futex syscall the value we are expecting. If `NotifyOne()` already
    // happened, it returns immediately.
    if (auto status = futex_.WaitUntil(deadline); !status.ok()) {
      // We need to lock on every exit path.
      (void)(mutex->Lock());
      return status;
    }
    // Lock before checking the condition again so that the notify thread cannot
    // change the condition data in the meantime.
    INTRINSIC_RT_RETURN_IF_ERROR(mutex->Lock());
  }
  // Condition is fulfilled.
  return OkStatus();
}

}  // namespace intrinsic::icon
