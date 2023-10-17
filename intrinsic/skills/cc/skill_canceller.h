// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_SKILL_CANCELLER_H_
#define INTRINSIC_SKILLS_CC_SKILL_CANCELLER_H_

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

// Supports cooperative cancellation of skills by the skill service.
//
// When a cancellation request is received, the skill should:
// 1) stop as soon as possible and leave resources in a safe and recoverable
//    state;
// 2) Return absl::CancelledError.
//
// The skill must call Ready() once it is ready to be cancelled.
//
// A skill can implement cancellation in one of two ways:
// 1) Poll cancelled(), and safely cancel if and when it becomes true.
// 2) Register a callback via RegisterCallback(). This callback will be invoked
//    when the skill receives a cancellation request.
class SkillCanceller {
 public:
  virtual ~SkillCanceller() = default;

  // True if the skill has received a cancellation request.
  virtual bool cancelled() = 0;

  // Signals that the skill is ready to be cancelled.
  virtual void Ready() = 0;

  // Sets a callback that will be invoked when a cancellation is requested.
  //
  // Only one callback may be registered, and the callback will be called at
  // most once. It must be registered before calling Ready().
  virtual absl::Status RegisterCallback(
      absl::AnyInvocable<absl::Status() const> callback) = 0;

  // Waits for the skill to be cancelled.
  //
  // Returns true if the skill was cancelled.
  virtual bool Wait(absl::Duration timeout) = 0;
};

// A SkillCanceller used by the skill service to cancel skills.
class SkillCancellationManager : public SkillCanceller {
 public:
  explicit SkillCancellationManager(
      absl::Duration ready_timeout,
      absl::string_view operation_name = "operation");

  bool cancelled() override { return cancelled_.HasBeenNotified(); };

  // Sets the cancelled flag and calls the callback (if set).
  absl::Status Cancel();

  void Ready() override { ready_.Notify(); };

  absl::Status RegisterCallback(
      absl::AnyInvocable<absl::Status() const> callback) override;

  bool Wait(absl::Duration timeout) override {
    return cancelled_.WaitForNotificationWithTimeout(timeout);
  };

  // Waits for the skill to be ready for cancellation.
  absl::Status WaitForReady();

 private:
  absl::Mutex cancel_mu_;
  absl::Notification ready_;
  absl::Duration ready_timeout_;
  absl::Notification cancelled_;
  std::unique_ptr<absl::AnyInvocable<absl::Status() const>> callback_;

  std::string operation_name_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_CANCELLER_H_
