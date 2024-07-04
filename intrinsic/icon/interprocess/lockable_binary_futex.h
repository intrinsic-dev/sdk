// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_LOCKABLE_BINARY_FUTEX_H_
#define INTRINSIC_ICON_INTERPROCESS_LOCKABLE_BINARY_FUTEX_H_

#include <cstddef>

#include "absl/base/attributes.h"
#include "absl/base/thread_annotations.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/binary_futex.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Wrapper around BinaryFutex so that it can be used like a common mutex. It
// also implements the compiler attributes so that the mutex compile time checks
// work (e.g. ABSL_GUARDED_BY).
//
// Caution: This class does not check if Lock()/Unlock() was called from the
// same thread! Whenever possible, use the `ScopedLock`!
class ABSL_LOCKABLE LockableBinaryFutex {
 public:
  // If `private_futex` is true, the futex can only be used from the current
  // process. This can have performance benefits. If the futex is used in a
  // shared memory segment, set `private_futex` to false.
  explicit LockableBinaryFutex(bool private_futex = false)
      : futex_(/*posted = */ true,  // Set `posted` so that the user can and
                                    // must call `Lock()` before `Unlock()`.
               private_futex) {}
  LockableBinaryFutex(const LockableBinaryFutex &) = delete;
  LockableBinaryFutex(LockableBinaryFutex &&) = default;
  ~LockableBinaryFutex() {
    // Check that the futex was unlocked.
    CHECK_EQ(futex_.Value(), 1) << "Futex was not unlocked before destruction";
  }

  // Blocks the calling thread, if necessary, until this `BinaryFutex` is free,
  // and then acquires it exclusively (This lock is also known as a "write
  // lock.").
  //
  // Forwards error of BinaryFutex::WaitUntil().
  RealtimeStatus Lock()
      ABSL_EXCLUSIVE_LOCK_FUNCTION() INTRINSIC_NON_REALTIME_ONLY {
    return futex_.WaitUntil(absl::InfiniteFuture());
  }

  // Releases this `BinaryFutex` and returns it from the exclusive/write state
  // to the free state. Calling thread must hold the `BinaryFutex` exclusively.
  // Forwards error of BinaryFutex::Post() and returns an error if the futex is
  // not held at the start of the function.
  RealtimeStatus Unlock() ABSL_UNLOCK_FUNCTION() {
    if (!IsHeld()) {
      return RealtimeStatus(absl::StatusCode::kFailedPrecondition,
                            "Futex is not locked");
    }
    return futex_.Post();
  }

  // If the mutex can be acquired without blocking, does so exclusively and
  // returns `true`. Otherwise, returns `false`.
  // Forwards error of BinaryFutex::TryWait().
  ABSL_MUST_USE_RESULT bool TryLock() INTRINSIC_CHECK_REALTIME_SAFE
      ABSL_EXCLUSIVE_TRYLOCK_FUNCTION(true) {
    return futex_.TryWait();
  }

  // Returns if the `BinaryFutex` is held.
  bool IsHeld() const { return futex_.Value() == 0; }

  // Asserts that the `BinaryFutex` is held.
  void AssertHeld() const ABSL_ASSERT_EXCLUSIVE_LOCK() { QCHECK(IsHeld()); }

 private:
  BinaryFutex futex_;
};

// RAII wrapper around `LockableBinaryFutex`.
class ABSL_SCOPED_LOCKABLE BinaryFutexLock {
 public:
  // Waits indefinitely for `mutex` to become available and locks it. There is
  // no order who will get the next lock in case multiple parties wait for the
  // lock. `mutex` must be non-null. Will fail fatally, if the futex syscall
  // fails.
  explicit BinaryFutexLock(LockableBinaryFutex *mutex)
      ABSL_EXCLUSIVE_LOCK_FUNCTION(mutex)
      : mutex_(mutex) {
    CHECK(mutex_ != nullptr);
    QCHECK_OK(mutex_->Lock());
  }
  BinaryFutexLock(const BinaryFutexLock &) = delete;
  BinaryFutexLock(BinaryFutexLock &&) = delete;
  void operator=(const BinaryFutexLock &) = delete;
  void operator=(BinaryFutexLock &&) = delete;
  ~BinaryFutexLock() ABSL_UNLOCK_FUNCTION() { CHECK_OK(mutex_->Unlock()); }
  // This class should *not* live on the heap. It should only live in the
  // current scope.
  void *operator new(std::size_t) = delete;
  void operator delete(void *) = delete;

 private:
  LockableBinaryFutex *mutex_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_LOCKABLE_BINARY_FUTEX_H_
