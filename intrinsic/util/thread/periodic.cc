// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/periodic.h"

#include <memory>
#include <utility>

#include "absl/base/thread_annotations.h"
#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/synchronization/mutex.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic {

PeriodicOperation::PeriodicOperation(absl::AnyInvocable<void()> f)
    : PeriodicOperation(std::move(f), absl::ZeroDuration()) {}
PeriodicOperation::PeriodicOperation(absl::AnyInvocable<void()> f,
                                     absl::Duration period)
    : PeriodicOperation(ThreadOptions(), std::move(f), period) {}
PeriodicOperation::PeriodicOperation(const ThreadOptions& options,
                                     absl::AnyInvocable<void()> f,
                                     absl::Duration period)
    : executor_thread_options_(options),
      operation_(std::move(f)),
      period_(period) {}

absl::Status PeriodicOperation::Start() {
  absl::MutexLock l(&mutex_);
  // Executor already started?
  if (operation_executor_ != nullptr) {
    return absl::OkStatus();
  }
  stop_notification_ = std::make_unique<absl::Notification>();
  operation_executor_ = std::make_unique<intrinsic::Thread>();
  INTR_RETURN_IF_ERROR(operation_executor_->Start(
      executor_thread_options_, &PeriodicOperation::ExecutorLoop, this));

  // Wait for the last start time to be something more recent than infinite
  // past, which would indicate the start of our first operation.
  absl::Condition wait_for_operation_start(
      +[](PeriodicOperation* op) ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
        return op->last_operation_start_time_ > absl::InfinitePast();
      },
      this);
  mutex_.Await(wait_for_operation_start);
  return absl::OkStatus();
}

absl::Status PeriodicOperation::Stop() {
  absl::MutexLock l(&mutex_);
  // Executor not running?
  if (operation_executor_ == nullptr) {
    return absl::OkStatus();
  }

  stop_notification_->Notify();
  mutex_.Unlock();
  operation_executor_->Join();
  mutex_.Lock();
  operation_executor_.reset(nullptr);
  stop_notification_.reset(nullptr);
  return absl::OkStatus();
}

void PeriodicOperation::ExecutorLoop() {
  // The next execution time is based on the time since the last execution
  // started.
  absl::Time next_execute_time = absl::Now();
  do {
    const absl::Time now = absl::Now();
    if (now > next_execute_time) {
      {
        absl::MutexLock l(&mutex_);
        last_operation_start_time_ = now;
      }
      operation_();

      // Catch up to the periodicity of this operation if the operation takes
      // longer than the period.
      if (period_ > absl::ZeroDuration()) {
        while (now > next_execute_time) {
          next_execute_time += period_;
        }
      }
    }

    const absl::Duration time_until_next_execution =
        next_execute_time - absl::Now();

    // Sleep for 3/4 of the time needed until the next execution to try to
    // avoid missing it when we can.
    if (time_until_next_execution > absl::ZeroDuration()) {
      absl::SleepFor(time_until_next_execution * 3 / 4);
    }
  } while (!stop_notification_->HasBeenNotified());
}

}  // namespace intrinsic
