// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_CANCELLER_H_
#define INTRINSIC_SKILLS_INTERNAL_CANCELLER_H_

#include <memory>
#include <string>

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"

namespace intrinsic {
namespace skills {

// Mediates communication between an operation that can be cancelled and a user
// that cancels it.
class Canceller {
 public:
  explicit Canceller(absl::Duration ready_for_cancellation_timeout,
                     absl::string_view operation_name = "operation");

  // Sets the cancelled flag and calls the cancellation callback (if set).
  absl::Status Cancel();

  // Returns true if a cancellation request has been received.
  bool Cancelled() { return cancelled_.HasBeenNotified(); }

  // Sets a callback that will be invoked when a cancellation is requested.
  //
  // Only one callback may be registered, and the callback will be called at
  // most once. It must be registered before calling
  // `NotifyReadyForCancellation`.
  absl::Status RegisterCancellationCallback(
      absl::AnyInvocable<absl::Status() const> callback);

  // Notifies the canceller that operation is ready to be cancelled.
  void NotifyReadyForCancellation() { ready_for_cancellation_.Notify(); }

 private:
  absl::Mutex cancel_mu_;
  absl::Notification ready_for_cancellation_;
  absl::Duration ready_for_cancellation_timeout_;
  absl::Notification cancelled_;
  std::unique_ptr<absl::AnyInvocable<absl::Status() const>>
      cancellation_callback_;

  std::string operation_name_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_CANCELLER_H_
