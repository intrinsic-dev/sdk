// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_PROMISE_H_
#define INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_PROMISE_H_

#include <atomic>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/synchronization/mutex.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/binary_futex.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/platform/common/buffers/rt_queue_buffer.h"

namespace intrinsic {

// Implementation of future and promise for message passing from a single
// (optionally real-time) thread to a single non-real-time thread. Use, i.e.,
// if a non-rt thread is waiting for an rt thread to eventually generate a
// value.
//
// Example:
//
// NonRealtimeFuture<bool> rt_job_result;
// Thread rt_thread;
// Thread::Options rt_thread_options;
// ASSIGN_OR_RETURN(auto promise, rt_job_result.GetPromise());
// RETURN_IF_ERROR(rt_thread.Start(rt_thread_options,
//                           [promise = std::move(promise)]() mutable {
//                             // Do fancy real time stuff that'll set the value
//                             // of `result`.
//                             // ...
//                             auto status = promise.SetValue(result);
//                           }));
// // Wait for the `rt_thread` to set the value on the promise.
// ASSIGN_OR_RETURN(bool job_result, rt_job_result.Get());
// rt_thread.Join();
//
// General notes:
// * The promise can only be moved, but not copied.
// * The future must always outlive any promise that may still be used,
//   even in cases when `Future::Get*` may have received a timeout.

// Forward declaration.
template <typename T>
class NonRealtimeFuture;

// The real-time capable promise.
// Can only be moved or (move-)assigned.
// While it's safe to always delete a promise (even if a future is waiting for
// its value), the lifetime of the corresponding future must outlive that of the
// promise.
template <typename T>
class RealtimePromise {
 public:
  RealtimePromise() = default;
  RealtimePromise(const RealtimePromise<T>&) = delete;
  RealtimePromise<T>& operator=(const RealtimePromise<T>&) = delete;
  RealtimePromise(RealtimePromise<T>&& promise)
      : buffer_(promise.buffer_),
        is_ready_(promise.is_ready_),
        is_cancel_acknowledged_(promise.is_cancel_acknowledged_),
        is_destroyed_(promise.is_destroyed_),
        is_cancelled_(promise.is_cancelled_) {
    // We need to set is_ready_ to a nullptr on a moved from object to ensure
    // that the destructor is still fully functional on moved from objects.
    promise.is_ready_ = nullptr;
  };
  RealtimePromise<T>& operator=(RealtimePromise<T>&& promise) {
    buffer_ = promise.buffer_;
    is_ready_ = promise.is_ready_;
    is_cancel_acknowledged_ = promise.is_cancel_acknowledged_;
    is_destroyed_ = promise.is_destroyed_;
    is_cancelled_ = promise.is_cancelled_;

    // We need to set is_ready_ to a nullptr on a moved from object to ensure
    // that the destructor is still fully functional on moved from objects.
    promise.is_ready_ = nullptr;
    return *this;
  };
  ~RealtimePromise<T>() {
    if (is_ready_ == nullptr) {
      // Destructing uninitialized promise.
      return;
    }
    // Signal the destruction of the promise to the future.
    auto post_error = is_destroyed_->Post();
    if (!post_error.ok()) {
      INTRINSIC_RT_LOG(ERROR)
          << "Failed to signal promise destruction: " << post_error.message();
    }
  }

  // Sets the value of the promise, which will make the future become ready.
  // Must only be called once. Not thread-safe.
  // Fails...
  //   * if the promise is uninitialized,
  //   * if its value has been previously been set, or
  //   * if the corresponding future was cancelled.
  icon::RealtimeStatus SetValue(const T& value) {
    if (buffer_ == nullptr) {
      if (is_ready_ == nullptr) {
        return icon::InvalidArgumentError(
            "SetValue called on uninitialized promise.");
      } else if (is_ready_->Value()) {
        return icon::ResourceExhaustedError(
            "SetValue must only be called once on a promise.");
      }
    } else if (is_cancelled_->load(std::memory_order_relaxed)) {
      // Acknowledge the cancellation.
      auto post_error = is_cancel_acknowledged_->Post();
      if (!post_error.ok()) {
        INTRINSIC_RT_LOG_THROTTLED(ERROR)
            << "Failed to acknowledge cancellation: " << post_error.message();
      }
      buffer_ = nullptr;
      return icon::CancelledError(
          "Corresponding future has already been cancelled.");
    }

    // Write the value to the buffer.
    T* element = buffer_->PrepareInsert();
    if (element == nullptr) {
      return icon::InternalError("Failed to prepare buffer insert.");
    }
    *element = value;
    buffer_->FinishInsert();
    // Reset `buffer_` to prevent repeated writes (if the logic above
    // changes).
    buffer_ = nullptr;
    // Preemptively confirm the cancellation so the future won't have to wait
    // on the promise when it's destructed.
    INTRINSIC_RT_RETURN_IF_ERROR(is_cancel_acknowledged_->Post());
    return is_ready_->Post();
  }

  // Cancels the promise and informs the corresponding future.
  // Fails if the promise is uninitialized. Not thread-safe.
  icon::RealtimeStatus Cancel() {
    if (buffer_ == nullptr) {
      return icon::InvalidArgumentError(
          "Cancel called on uninitialized promise.");
    }
    is_cancelled_->store(true, std::memory_order_relaxed);
    return is_cancel_acknowledged_->Post();
  }

 private:
  friend class NonRealtimeFuture<T>;

  // Constructor.
  // Does not take ownership of any pointers, thus all pointers must outlive the
  // promise.
  RealtimePromise(internal::RtQueueBuffer<T>* buffer,
                  icon::BinaryFutex* is_ready,
                  icon::BinaryFutex* is_cancel_acknowledged,
                  icon::BinaryFutex* is_destroyed,
                  std::atomic_bool* is_cancelled)
      : buffer_(buffer),
        is_ready_(is_ready),
        is_cancel_acknowledged_(is_cancel_acknowledged),
        is_destroyed_(is_destroyed),
        is_cancelled_(is_cancelled) {}

  // The buffer used for passing the value from the promise to the future.
  internal::RtQueueBuffer<T>* buffer_ = nullptr;
  // The future waits on this to receive a value.
  icon::BinaryFutex* is_ready_ = nullptr;
  // The future waits on this to make sure the promise has received a cancel
  // signal.
  icon::BinaryFutex* is_cancel_acknowledged_ = nullptr;
  // The future waits on this to make sure the promise has been destroyed.
  icon::BinaryFutex* is_destroyed_ = nullptr;
  // Whether the future/promise has been cancelled.
  std::atomic_bool* is_cancelled_ = nullptr;
};

// The non-real time capable future.
// Cannot be copied, moved, or (move-)assigned.
// The future must outlive its promise.
template <typename T>
class NonRealtimeFuture {
 public:
  NonRealtimeFuture()
      : buffer_(/*capacity=*/1),
        cancellation_confirm_timeout_(absl::Seconds(1)) {}
  explicit NonRealtimeFuture(absl::Duration cancellation_confirm_timeout)
      : buffer_(/*capacity=*/1),
        cancellation_confirm_timeout_(cancellation_confirm_timeout) {}

  NonRealtimeFuture(const NonRealtimeFuture<T>&) = delete;
  NonRealtimeFuture<T>& operator=(const NonRealtimeFuture<T>&) = delete;
  NonRealtimeFuture(NonRealtimeFuture<T>&& future) = delete;
  NonRealtimeFuture<T>& operator=(NonRealtimeFuture<T>&& future) = delete;
  ~NonRealtimeFuture() {
    absl::MutexLock lock(&synchronization_mutex_);
    if (promise_was_moved_) {
      // Cancel and wait for the promise to confirm and be destroyed.
      auto status = UnprotectedCancel();
      status = OverwriteIfNotInError(
          status, is_destroyed_.WaitFor(absl::InfiniteDuration()));
      if (!status.ok()) {
        LOG(ERROR) << "Failed to destroy future: " << status.message();
      }
    }
  }

  // Returns a promise that may then be moved around for the value to be set.
  // Must only be called once or will return an `AlreadyExistsError`.
  INTRINSIC_NON_REALTIME_ONLY absl::StatusOr<RealtimePromise<T>> GetPromise() {
    absl::MutexLock lock(&synchronization_mutex_);

    if (promise_was_moved_) {
      return icon::AlreadyExistsError(
          "GetPromise must only be called once on a future.");
    }
    promise_was_moved_ = true;
    return std::move(promise_);
  };

  // Waits until `deadline` for another thread to call `SetValue` on a promise.
  // Returns a ...
  //   * `DeadlineExceededError` if the promise does not report a value by
  //     `deadline`.
  //   * `CancelledError` if the promise has already been cancelled.
  //   * `ResourceExhaustedError` if it has successfully been called once
  //     already.
  // Remember that even on error, the future must outlive any associated
  // promise.
  INTRINSIC_NON_REALTIME_ONLY absl::StatusOr<T> GetWithDeadline(
      absl::Time deadline) {
    absl::MutexLock lock(&synchronization_mutex_);

    if (is_value_retrieved_) {
      return icon::ResourceExhaustedError("Value has already been retrieved.");
    }
    if (is_cancelled_.load(std::memory_order_relaxed)) {
      return absl::CancelledError("Future or promise have been cancelled.");
    }
    INTRINSIC_RT_RETURN_IF_ERROR(is_ready_.WaitUntil(deadline));
    is_value_retrieved_ = true;
    return *buffer_.Front();
  };

  // Waits until `timeout` for another thread to call `SetValue` on a promise.
  // Returns a ...
  //   * DeadlineExceededError` if the promise does not report a value before
  //     the `timeout`.
  //   * `CancelledError` if the promise has already been cancelled.
  //   * `ResourceExhaustedError` if it has successfully been called once
  //     already.
  // Remember that even on error, the future must outlive any associated
  // promise.
  INTRINSIC_NON_REALTIME_ONLY absl::StatusOr<T> GetWithTimeout(
      absl::Duration timeout) {
    return GetWithDeadline(absl::Now() + timeout);
  }

  // Waits (indefinitely) for another thread to call `SetValue` on a promise.
  // Returns a ...
  //   * `CancelledError` if the promise has already been cancelled.
  //   * `ResourceExhaustedError` if it has successfully been called once
  //     already.
  // Remember that even on error, the future must outlive that of any associated
  // promise.
  INTRINSIC_NON_REALTIME_ONLY absl::StatusOr<T> Get() {
    return GetWithDeadline(absl::InfiniteFuture());
  };

  // Returns true if the value is available and a call to `Get*` would return
  // immediately.
  bool IsReady() {
    absl::MutexLock lock(&synchronization_mutex_);
    return !buffer_.Empty();
  }

  // Cancels the future and waits for the promise to confirm.
  // The promise may confirm by ...
  //   * calling its `SetValue()` method.
  //   * calling its `Cancel()` method.
  // Returns a `DeadlineExceededError` if the promise did not confirm within the
  // cancellation confirmation timeout.
  INTRINSIC_NON_REALTIME_ONLY absl::Status Cancel() {
    absl::MutexLock lock(&synchronization_mutex_);
    return UnprotectedCancel();
  }

 private:
  // Non thread-safe implementation for cancelling the future.
  // Called in cases where the `synchronization_mutex_` is already held.
  INTRINSIC_NON_REALTIME_ONLY absl::Status UnprotectedCancel() {
    bool was_cancelled =
        is_cancelled_.exchange(true, std::memory_order_relaxed);
    if (!was_cancelled) {
      INTRINSIC_RT_RETURN_IF_ERROR(
          is_cancel_acknowledged_.WaitFor(cancellation_confirm_timeout_));
    }
    return absl::OkStatus();
  }

  // Used for passing the value from the promise to the future.
  internal::RtQueueBuffer<T> buffer_;
  // Used by the future to wait for the value (and the promise to set the
  // value).
  icon::BinaryFutex is_ready_;
  // Used by future to wait for the promise to acknowledge the cancellation.
  icon::BinaryFutex is_cancel_acknowledged_;
  // Used by future to wait for the promise to be destroyed.
  icon::BinaryFutex is_destroyed_;
  // Whether the future/promise has been cancelled.
  std::atomic_bool is_cancelled_;
  // Whether the value has been retrieved from the future.
  bool is_value_retrieved_ = false;
  // The promise has this much time to confirm the future's cancellation.
  absl::Duration cancellation_confirm_timeout_;
  // The corresponding promise that may be retrieved via `GetPromise()`.
  RealtimePromise<T> promise_ =
      RealtimePromise<T>(/*buffer=*/&buffer_, /*is_ready=*/&is_ready_,
                         /*is_cancel_acknowledged=*/&is_cancel_acknowledged_,
                         /*is_destroyed=*/&is_destroyed_,
                         /*is_cancelled=*/&is_cancelled_);
  // Indicates whether the promise has been retrieved through `GetPromise`.
  bool promise_was_moved_ = false;
  // Mutex to ensure reentrancy and thread-safety.
  absl::Mutex synchronization_mutex_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_COMMON_BUFFERS_RT_PROMISE_H_
