// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_CONDITION_VARIABLE_H_
#define INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_CONDITION_VARIABLE_H_

#include "absl/base/thread_annotations.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/binary_futex.h"
#include "intrinsic/icon/interprocess/lockable_binary_futex.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Condition variable for BinaryFutexes for use in realtime scenarios (only
// `NotifyOne()` should be called from the realtime thread) in
// multiple-producer-single-consumer scenarios.
//
//
// Note: The user must make sure that no thread is waiting using `Await()` when
// this class gets destroyed.
//
// Example usage:
// // Helper data structure using an integer as condition state. Makes sure that
// // the condition state is protected by a mutex.
// ConditionVariableData<int> data(0);
// intrinsic::Thread producer([&] {
//   {
//     // The condition state must be protected with the same mutex as used for
//     // Await().
//     BinaryFutexLock lock(&data.mutex);
//     data.state = 0;
//   }
//   // Condition is not fulfilled. So consumer will continue to wait.
//   data.condition_variable.NotifyOne();
//   {
//     BinaryFutexLock lock(&data.mutex);
//     data.state = 1;
//     // Condition is now fulfilled, but we need to notify the consumer.
//   }
//   // The consumer thread has either arrived at waiting and needs the notify
//   // or enters waiting later and checks the condition immediately.
//   data.condition_variable.NotifyOne();
// });
//
// intrinsic::Thread consumer([&] {
//   BinaryFutexLock lock(&data.mutex);
//   data.condition_variable.Await(
//       &data.mutex,
//       absl::Condition(+[](int *state) { return *state == 1; }, &data.state));
// });
class BinaryFutexConditionVariable {
 public:
  // If `private_futex` is true, the futex can only be used from the current
  // process. This can have performance benefits. If the futex is used in a
  // shared memory segment, set `private_futex` to false.
  explicit BinaryFutexConditionVariable(bool private_futex = false)
      : futex_(/*posted = */ false, private_futex) {}
  BinaryFutexConditionVariable(const BinaryFutexConditionVariable &) = delete;
  BinaryFutexConditionVariable(BinaryFutexConditionVariable &&) = default;
  ~BinaryFutexConditionVariable() = default;

  // Notifies one thread currently waiting in `Await()`. It is not specified
  // which thread will be notified. If no thread is waiting, there is no
  // effect and the function returns.
  //
  // NotifyAll is not available since it would make the implementation more
  // complicated.
  RealtimeStatus NotifyOne() INTRINSIC_CHECK_REALTIME_SAFE {
    return futex_.Post();
  }

  // Waits for `condition` to become true. `mutex` must protect the
  // variables used in `condition`. This function only checks `condition`
  // initially or whenever some other thread calls `NotifyOne()` on `this`.
  //
  // `mutex` must be held when calling this function.
  //
  // `mutex` will be unlocked while waiting and relocked before returning.
  //
  //
  // If `condition` is already fulfilled, returns OK regardless whether the
  // deadline has already passed.
  //
  // If `deadline` is reached while waiting, this function returns a
  // DeadlineExceeded error regardless whether the condition is fulfilled at
  // this moment.
  //
  // WARNING: Another thread can deadlock this function by holding on to
  // `mutex`, up to and including missing `deadline`!
  //
  // If this class returns other errors than DeadlineExceeded, it is likely
  // that this instance is in an unusable state.
  //
  RealtimeStatus Await(LockableBinaryFutex *mutex, absl::Condition condition,
                       absl::Time deadline)
      ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex);

  // Same as other version, but with a timeout.
  RealtimeStatus Await(LockableBinaryFutex *mutex, absl::Condition condition,
                       absl::Duration timeout = absl::InfiniteDuration())
      ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex) {
    return Await(mutex, condition, absl::Now() + timeout);
  }

 private:
  BinaryFutex futex_;
};

// Helper data structure for a condition variable that makes sure that the
// condition state is protected by a mutex.
template <typename StateType>
struct ConditionVariableData {
  ConditionVariableData() = default;
  explicit ConditionVariableData(const StateType &&initial_state,
                                 bool private_futex = false)
      : mutex(private_futex),
        condition_variable(private_futex),
        state(initial_state) {}
  // Mutex to protect the condition state.
  LockableBinaryFutex mutex;
  // The condition variable using state.
  BinaryFutexConditionVariable condition_variable;
  // The state that the condition variable waits for.
  StateType state ABSL_GUARDED_BY(mutex) = 0;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_CONDITION_VARIABLE_H_
