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

SkillCancellationManager::SkillCancellationManager(
    const absl::Duration ready_timeout, const absl::string_view operation_name)
    : ready_timeout_(ready_timeout), operation_name_(operation_name) {}

absl::Status SkillCancellationManager::Cancel() {
  INTRINSIC_RETURN_IF_ERROR(WaitForReady());

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

  if (callback_ != nullptr) {
    INTRINSIC_RETURN_IF_ERROR((*callback_)());
  }

  return absl::OkStatus();
}

absl::Status SkillCancellationManager::RegisterCallback(
    absl::AnyInvocable<absl::Status() const> callback) {
  absl::MutexLock lock(&cancel_mu_);
  if (ready_.HasBeenNotified()) {
    return absl::FailedPreconditionError(
        absl::Substitute("A callback cannot be registered after"
                         "$0 is ready for cancellation.",
                         operation_name_));
  }
  if (callback_ != nullptr) {
    return absl::AlreadyExistsError("A callback was already registered.");
  }
  callback_ = std::make_unique<absl::AnyInvocable<absl::Status() const>>(
      std::move(callback));

  return absl::OkStatus();
}

absl::Status SkillCancellationManager::WaitForReady() {
  if (!ready_.WaitForNotificationWithTimeout(ready_timeout_)) {
    return absl::DeadlineExceededError(absl::Substitute(
        "Timed out waiting for $0 to be ready for cancellation.",
        operation_name_));
  }

  return absl::OkStatus();
}

}  // namespace skills
}  // namespace intrinsic
