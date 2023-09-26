// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/cc/skill_canceller.h"

#include <memory>
#include <utility>

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/strings/substitute.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/time.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {
namespace skills {

Canceller::Canceller(const absl::Duration ready_for_cancellation_timeout,
                     const absl::string_view operation_name)
    : ready_for_cancellation_timeout_(ready_for_cancellation_timeout),
      operation_name_(operation_name) {}

absl::Status Canceller::Cancel() {
  // Wait for the operation to be ready for cancellation.
  if (!ready_for_cancellation_.WaitForNotificationWithTimeout(
          ready_for_cancellation_timeout_)) {
    return absl::DeadlineExceededError(absl::Substitute(
        "Timed out waiting for $0 to be ready for cancellation.",
        operation_name_));
  }

  // Calling the user callback with the lock held would lead to a deadlock if
  // the callback never returns, so we only keep the lock for the notification.
  {
    absl::MutexLock lock(&cancel_mu_);
    if (cancelled_.HasBeenNotified()) {
      return absl::FailedPreconditionError(
          absl::Substitute("$0 was already cancelled.", operation_name_));
    }

    cancelled_.Notify();
  }

  if (cancellation_callback_ != nullptr) {
    INTRINSIC_RETURN_IF_ERROR((*cancellation_callback_)());
  }

  return absl::OkStatus();
}

absl::Status Canceller::RegisterCancellationCallback(
    absl::AnyInvocable<absl::Status() const> callback) {
  absl::MutexLock lock(&cancel_mu_);
  if (ready_for_cancellation_.HasBeenNotified()) {
    return absl::FailedPreconditionError(
        absl::Substitute("A cancellation callback cannot be registered after"
                         "$0 is ready for cancellation.",
                         operation_name_));
  }
  if (cancellation_callback_ != nullptr) {
    return absl::AlreadyExistsError(
        "A cancellation callback was already registered.");
  }
  cancellation_callback_ =
      std::make_unique<absl::AnyInvocable<absl::Status() const>>(
          std::move(callback));

  return absl::OkStatus();
}

}  // namespace skills
}  // namespace intrinsic
