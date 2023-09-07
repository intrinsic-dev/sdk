// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/util/thread/lockstep.h"

#include <utility>

#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/remote_trigger/binary_futex.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"

namespace intrinsic {
Lockstep &Lockstep::operator=(Lockstep &&other) {
  if (this != &other) {
    a_finished_ = std::exchange(other.a_finished_, icon::BinaryFutex(false));
    b_finished_ =
        std::exchange(other.b_finished_, icon::BinaryFutex(/*posted=*/true));
    state_.store(other.state_.load());
  }
  return *this;
}

icon::RealtimeStatus Lockstep::StartOperationAWithDeadline(
    absl::Time deadline) {
  INTRINSIC_RT_RETURN_IF_ERROR(b_finished_.WaitUntil(deadline));
  if (state_ == State::kCancelled) {
    // Ignore error because returning Aborted to the caller is more important.
    (void)b_finished_.Post();
    return icon::AbortedError(
        "Not starting operation A: lockstep has been cancelled");
  }
  if (state_ != State::kBFinished) {
    return icon::FailedPreconditionError("Expected State::kBFinished");
  }
  state_ = State::kARunning;
  return icon::OkStatus();
}

icon::RealtimeStatus Lockstep::StartOperationAWithTimeout(
    absl::Duration timeout) {
  return StartOperationAWithDeadline(absl::Now() + timeout);
}

icon::RealtimeStatus Lockstep::EndOperationA() {
  if (state_ == State::kCancelled) {
    return icon::OkStatus();
  }
  if (state_ != State::kARunning) {
    return icon::FailedPreconditionError(
        "Mismatched call to EndOperationA. Did you call StartOperationA...?");
  }
  state_ = State::kAFinished;
  return a_finished_.Post();
}

icon::RealtimeStatus Lockstep::StartOperationBWithDeadline(
    absl::Time deadline) {
  INTRINSIC_RT_RETURN_IF_ERROR(a_finished_.WaitUntil(deadline));
  if (state_ == State::kCancelled) {
    // Ignore error because returning Aborted to the caller is more important.
    (void)a_finished_.Post();
    return icon::AbortedError(
        "Not starting operation B: lockstep has been cancelled");
  }
  if (state_ != State::kAFinished) {
    return icon::FailedPreconditionError("Expected State::kAFinished");
  }
  state_ = State::kBRunning;
  return icon::OkStatus();
}

icon::RealtimeStatus Lockstep::StartOperationBWithTimeout(
    absl::Duration timeout) {
  return StartOperationBWithDeadline(absl::Now() + timeout);
}

icon::RealtimeStatus Lockstep::EndOperationB() {
  if (state_ == State::kCancelled) {
    return icon::OkStatus();
  }
  if (state_ != State::kBRunning) {
    return icon::FailedPreconditionError(
        "Mismatched call to EndOperationB. Did you call StartOperationB...?");
  }
  state_ = State::kBFinished;
  return b_finished_.Post();
}

void Lockstep::Cancel() {
  state_ = State::kCancelled;
  if (auto status = a_finished_.Post(); !status.ok()) {
    INTRINSIC_RT_LOG_THROTTLED(ERROR) << status.message();
  }
  if (auto status = b_finished_.Post(); !status.ok()) {
    INTRINSIC_RT_LOG_THROTTLED(ERROR) << status.message();
  }
}

icon::RealtimeStatus Lockstep::Reset(absl::Duration timeout) {
  if (state_ != State::kCancelled) {
    return icon::FailedPreconditionError("Reset expects a cancelled lockstep.");
  }
  // Acquire both futexes, so that any call to a `StartOperation...` function
  // will have to wait until the reset is done.
  INTRINSIC_RT_RETURN_IF_ERROR(a_finished_.WaitFor(timeout));
  INTRINSIC_RT_RETURN_IF_ERROR(b_finished_.WaitFor(timeout));
  state_ = State::kBFinished;
  // Let `StartOperationA...` be next.
  INTRINSIC_RT_RETURN_IF_ERROR(b_finished_.Post());
  return icon::OkStatus();
}

}  // namespace intrinsic
