// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_H_
#define INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_H_

#include <atomic>
#include <cstdint>

#include "absl/time/time.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// A BinaryFutex class implements logic to signal between two high-performance
// processes. The futex implementation has similar semantics to a binary
// semaphore and can be shared through multiple processes via shared memory.
//
// The example below shows how a pair of binary futexes can be used to set up a
// client-server model:
//
// ```
//  const std::string request_id = "/test_futex_request";
//  const std::string response_id = "/test_futex_response";
//
//  intrinsic::icon::SharedMemoryManager shm_manager;
//  INTRINSIC_RETURN_IF_ERROR(shm_manager.AddSegment(request_id,
//  BinaryFutex()));
//  INTRINSIC_RETURN_IF_ERROR(shm_manager.AddSegment(response_id,
//  BinaryFutex()));
//
//  auto pid = fork();
//  if (pid == -1) {
//    return absl::InternalError(strerror(errno));
//  }
//
//  // Server process
//  if (pid == 0) {
//    INTRINSIC_ASSIGN_OR_RETURN(
//        auto f_request,
//        intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
//    INTRINSIC_ASSIGN_OR_RETURN(
//        auto f_response,
//        intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(response_id));
//
//    while (true) {
//      INTRINSIC_RETURN_IF_ERROR(f_request.GetValue().WaitFor());
//      LOG(INFO) << "Server received request. Doing some work...";
//      INTRINSIC_RETURN_IF_ERROR(f_response.GetValue().Post());
//    }
//  }
//
//  // Client process
//  INTRINSIC_ASSIGN_OR_RETURN(
//      auto f_request,
//      intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
//  INTRINSIC_ASSIGN_OR_RETURN(
//      auto f_response,
//      intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(response_id));
//  for (int j = 0; j < 10; j++) {
//    INTRINSIC_RETURN_IF_ERROR(f_request.GetValue().Post());
//    LOG(INFO) << "Waiting on server to finish some work.";
//    INTRINSIC_RETURN_IF_ERROR(f_response.GetValue().WaitFor());
//  }
// ```
//
// More details can be found under
// https://man7.org/linux/man-pages/man2/futex.2.html
//
class BinaryFutex {
 public:
  // Constructors.
  explicit BinaryFutex(bool posted = false);
  BinaryFutex(BinaryFutex &other) = delete;
  BinaryFutex &operator=(const BinaryFutex &other) = delete;
  BinaryFutex(BinaryFutex &&other);
  BinaryFutex &operator=(BinaryFutex &&other);

  // Posts on the futex and increases its value to one.
  // If the current value is already one, the value will not furher increase.
  // Returns an internal error if the futex could not be increased.
  // Real-time safe.
  // Thread-safe.
  RealtimeStatus Post();

  // Waits until the futex becomes one or the deadline exceeds.
  // When futex becomes one, immediately sets it to zero and returns ok.
  // Returns an internal error if the futex could not be accessed.
  // Real-time safe when `deadline` is close enough.
  // Thread-safe.
  RealtimeStatus WaitUntil(absl::Time deadline) const;

  // Waits until the futex becomes one or the timeout exceeds.
  // When futex becomes one, immediately sets it to zero and returns ok.
  // Returns an internal error if the futex could not be accessed.
  // Real-time safe when `timeout` is short enough.
  // Thread-safe.
  RealtimeStatus WaitFor(absl::Duration timeout) const;

  // Returns the current value of the futex.
  // This can either be zero or one. The returned value might be outdated by the
  // time the caller uses the value.
  // Real-time safe.
  uint32_t Value() const;

 private:
  // The atomic value is marked as mutable to create a const correct public
  // interface to the futex class. A call to wait has read-only semantics while
  // a call to post has write semantics.
  static_assert(
      std::atomic<uint32_t>::is_always_lock_free,
      "Atomic operations need to be lock free for multi-process communication");
  mutable std::atomic<uint32_t> val_ = {0};
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_H_
