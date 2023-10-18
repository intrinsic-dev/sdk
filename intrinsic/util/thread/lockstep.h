// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_LOCKSTEP_H_
#define INTRINSIC_UTIL_THREAD_LOCKSTEP_H_

#include <atomic>

#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/binary_futex.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic {

// Lockstep is a synchronization primitive that can be used to force two threads
// to operate in lock step.
//
// Code between `StartOperationA...` and `EndOperationA` is referred to as
// "Operation A". Code between `StartOperationB...` and `EndOperationB` is
// referred to as "Operation B".
//
// The Lockstep class ensures that these operations are performed (to
// completion, with mutual exclusion) in the following order:
//
//    Operation A
//    Operation B
//    Operation A
//    Operation B
//    ...
//
// Attempts to perform these operations in any other order will block on either
// `StartOperationA...` or `StartOperationB...`.
//
// Essentially, it implements the following state machine:
//
// ====== Operation A =======| === Operation B ===
//        StartOperationB()  |
//    ┌──────────┐      ╲    |     ┌──────────┐
//    │kAFinished│ ----------|---> │kBRunning │
//    └──────────┘           |     └──────────┘
//         ^                 |          |
//         | EndOperationA() |          | EndOperationB()
//         |                 |          v
//    ┌──────────┐           |     ┌──────────┐
//    │kARunning │ <---------|---- │kBFinished│ <---- Start
//    └──────────┘           |  ╲  └──────────┘
//                       StartOperationA()
//
// The implementation is designed to be efficient (using low-level futexes) and
// is intended for realtime use.
class Lockstep {
 public:
  static constexpr absl::Duration kResetTimeout = absl::Seconds(1);

  Lockstep() = default;
  Lockstep(Lockstep &other) = delete;
  Lockstep &operator=(const Lockstep &other) = delete;
  Lockstep(Lockstep &&other) = delete;
  Lockstep &operator=(Lockstep &&other);

  // Blocks the current thread until Operation A is ready to begin or timeout
  // has expired. Similar to StartOperationAWithDeadline except that this uses a
  // timeout instead of a deadline.
  //
  // Returns early when `Cancel()` has been called.
  // For concurrent calls, only one `StartOperationA...()` returns.
  //
  // Returns `OkStatus` on success. Otherwise, returns an error, in which case
  // user code *should not* perform Operation A. Returns `kAborted` if
  // `Cancel()` has been called. Returns `kDeadlineExceeded` if the underlying
  // Futex wait timed out or `kInternal` in case of an internal futex error.
  icon::RealtimeStatus StartOperationAWithTimeout(absl::Duration timeout);

  // Blocks the current thread until Operation A is ready to begin or the
  // deadline has expired. Similar to StartOperationAWithTimeout except that
  // this uses a deadline instead of a timeout.
  //
  // Returns early when `Cancel()` has been called.
  // For concurrent calls, only one `StartOperationA...()` returns.
  //
  // Returns `OkStatus` on success. Otherwise, returns an error, in which case
  // user code *should not* perform Operation A. Returns `kAborted` if
  // `Cancel()` has been called. Returns `kDeadlineExceeded` if the underlying
  // Futex wait timed out or `kInternal` in case of an internal futex error.
  icon::RealtimeStatus StartOperationAWithDeadline(absl::Time deadline);

  // Signals that Operation A has completed, potentially waking a thread that is
  // waiting on `StartOperationB...()`.
  //
  // Returns `OkStatus` on success (including if `Cancel()` has been called).
  // Returns `kFailedPrecondition` if a matching StartOperationA...() has not
  // been called.
  icon::RealtimeStatus EndOperationA();

  // Blocks the current thread until Operation B is ready to begin or timeout
  // has expired. Similar to StartOperationBWithDeadline except that this uses a
  // timeout instead of a deadline.
  //
  // Returns early when `Cancel()` has been called.
  // For concurrent calls, only one `StartOperationB...()` returns.
  //
  // Returns `OkStatus` on success. Otherwise, returns an error, in which case
  // user code *should not* perform Operation B. Returns `kAborted` if
  // `Cancel()` has been called. Returns `kDeadlineExceeded` if the underlying
  // Futex wait timed out or `kInternal` in case of an internal futex error.
  icon::RealtimeStatus StartOperationBWithTimeout(absl::Duration timeout);

  // Blocks the current thread until Operation B is ready to begin or the
  // deadline has expired. Similar to StartOperationBWithTimeout except that
  // this uses a deadline instead of a timeout.
  //
  // Returns early when `Cancel()` has been called.
  // For concurrent calls, only one `StartOperationB...()` returns.
  //
  // Returns `OkStatus` on success. Otherwise, returns an error, in which case
  // user code *should not* perform Operation B. Returns `kAborted` if
  // `Cancel()` has been called. Returns `kDeadlineExceeded` if the underlying
  // Futex wait timed out or `kInternal` in case of an internal futex error.
  icon::RealtimeStatus StartOperationBWithDeadline(absl::Time deadline);

  // Signals that Operation B has completed, potentially waking a thread that is
  // waiting on `StartOperationA...()`.
  //
  // Returns `OkStatus` on success (including if `Cancel()` has been called).
  // Returns `kFailedPrecondition` if a matching StartOperationB...() has not
  // been called.
  icon::RealtimeStatus EndOperationB();

  // Signals to all threads waiting on either `StartOperationA...()` or
  // `StartOperationB...()` to wake up and return `kAborted`. All subsequent
  // calls to `StartOperationA...()` and `StartOperationB...()` will return
  // `kAborted` until `Reset()` is called.
  void Cancel();

  // Resets the lockstep to its initial state.
  // Must only be called after `Cancel`, and thus should not be called
  // inside any Operation. Returns an error if setting the futexes times out or
  // if the lockstep is not cancelled.
  icon::RealtimeStatus Reset(absl::Duration timeout = kResetTimeout);

 private:
  enum class State : char {
    kBFinished,
    kARunning,
    kAFinished,
    kBRunning,
    kCancelled
  };
  icon::BinaryFutex a_finished_{/*posted=*/false};
  icon::BinaryFutex b_finished_{/*posted=*/true};
  std::atomic<State> state_ = State::kBFinished;
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_LOCKSTEP_H_
