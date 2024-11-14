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
//  INTR_RETURN_IF_ERROR(shm_manager.AddSegment(request_id, BinaryFutex()));
//  INTR_RETURN_IF_ERROR(shm_manager.AddSegment(response_id, BinaryFutex()));
//
//  auto pid = fork();
//  if (pid == -1) {
//    return absl::InternalError(strerror(errno));
//  }
//
//  // Server process
//  if (pid == 0) {
//    INTR_ASSIGN_OR_RETURN(
//        auto f_request,
//        intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
//    INTR_ASSIGN_OR_RETURN(
//        auto f_response,
//        intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(response_id));
//
//    while (true) {
//      INTR_RETURN_IF_ERROR(f_request.GetValue().WaitFor());
//      LOG(INFO) << "Server received request. Doing some work...";
//      INTR_RETURN_IF_ERROR(f_response.GetValue().Post());
//    }
//  }
//
//  // Client process
//  INTR_ASSIGN_OR_RETURN(
//      auto f_request,
//      intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(request_id));
//  INTR_ASSIGN_OR_RETURN(
//      auto f_response,
//      intrinsic::icon::ReadWriteMemorySegment<BinaryFutex>::Get(response_id));
//  for (int j = 0; j < 10; j++) {
//    INTR_RETURN_IF_ERROR(f_request.GetValue().Post());
//    LOG(INFO) << "Waiting on server to finish some work.";
//    INTR_RETURN_IF_ERROR(f_response.GetValue().WaitFor());
//  }
// ```
//
// More details can be found under
// https://man7.org/linux/man-pages/man2/futex.2.html
//
class BinaryFutex {
 public:
  // These constants aren't enum values, because `static_cast`ing them to
  // uint32_t everywhere would only make the implementation of BinaryFutex
  // unnecessarily verbose and harder to read.

  // This is the base state of the futex (unless it is constructed with
  // `posted == true`). A successful call to Wait() will reset the futex to this
  // value.
  static constexpr uint32_t kReady = 0;
  // Calling `Post()` on a `BinaryFutex` writes this value to the underlying
  // variable.
  static constexpr uint32_t kPosted = 1;
  // Calling `Close()` on a `BinaryFutex` writes this value to the underlying
  // variable. This state is final, i.e. a BinaryFutex that is `kClosed` will
  // never change to another state afterwards.
  static constexpr uint32_t kClosed = 2;

  // `posted` sets the initial value of the futex, i.e. if set to
  // true it equals calling `Post()`.
  // Set `private_futex` to true, if the futex is only used in one process, e.g.
  // it does not live in a shared memory segment. This can give some performance
  // benefits.
  explicit BinaryFutex(bool posted = false, bool private_futex = false);
  BinaryFutex(BinaryFutex &other) = delete;
  BinaryFutex &operator=(const BinaryFutex &other) = delete;
  BinaryFutex(BinaryFutex &&other);
  BinaryFutex &operator=(BinaryFutex &&other);
  ~BinaryFutex();

  // Posts on the futex and increases its value to one.
  // If the current value is already one, the value will not further increase.
  // If the value changed, this wakes up to one thread waiting on this
  // BinaryFutex.
  //
  // Returns an internal error if the futex could not be increased.
  // Real-time safe.
  // Thread-safe.
  RealtimeStatus Post();

  // Waits until the futex becomes `kPosted`, `kClosed` or the deadline expires.
  // As soon as the futex takes either of the two values above, or if the futex
  // already *has* that value when this function starts, this function
  // immediately sets the futex to `kReady` and returns OkStatus. Checks the
  // futex before checking the deadline. So if the futex is already `kPosted` or
  // `kClosed`, the deadline is not checked.
  //
  // Returns InternalError if the futex could not be accessed.
  // Returns AbortedError if the futex is `kClosed`.
  // Returns DeadlineExceededError if the futex does not become either `kPosted`
  // or `kClosed` within the deadline.
  // Returns OkStatus and resets the futex to `kReady` on success (if the futex
  // already is or becomes `kPosted` before the deadline).
  //
  // Real-time safe when `deadline` is close enough.
  // Thread-safe.
  RealtimeStatus WaitUntil(absl::Time deadline) const;

  // Waits until the futex becomes `kPosted`, `kClosed` or the timeout expires.
  // As soon as the futex takes either of the two values above, or if the futex
  // already *has* that value when this function starts, this function
  // immediately sets the futex to `kReady` and returns OkStatus. Checks the
  // futex before checking the timeout. So if the futex is already `kPosted` or
  // `kClosed`, the timeout is not checked.
  //
  // Returns InternalError if the futex could not be accessed.
  // Returns AbortedError if the futex is `kClosed`.
  // Returns DeadlineExceededError if the futex does not become either `kPosted`
  // or `kClosed` within the timeout.
  // Returns OkStatus and resets the futex to `kReady` on success (if the futex
  // already is or becomes `kPosted` before the timeout).
  //
  // Real-time safe when `timeout` is close enough.
  // Thread-safe.
  RealtimeStatus WaitFor(absl::Duration timeout) const;

  // Checks (without blocking) whether the current value of the futex indicates
  // that it has been `Post()`ed.
  // If it does, this function (atomically!) resets the futex value.
  //
  // Returns true if the futex was `Post()`ed (and this function subsequently
  // reset the value).
  // Returns false if the futex wasn't `Post()`ed. This can happen for two
  // reasons: Either the futex wasn't `Post()`ed _yet_, or it is closed (see
  // `Close()` below) and never will be `Post()`ed.
  bool TryWait() const;

  // Returns the current value of the futex.
  // This can either be kReady, kPosted or kClosed. The returned value might be
  // outdated by the time the caller uses the value.
  //
  // Real-time safe.
  uint32_t Value() const;

  // Marks this BinaryFutex as closed. Any subsequent calls to `Post()`,
  // `TryWait()`, `WaitFor()` or `WaitUntil()` will *immediately* return
  // AbortedError (or, in `TryWait()`'s case, `false`).
  //
  // Like `Post()`, this wakes up to one waiting thread, so if there is an
  // ongoing call to `WaitUntil()` or `WaitFor()`, that call will end and return
  // AbortedError.
  void Close();

 private:
  // The atomic value is marked as mutable to create a const correct public
  // interface to the futex class. A call to wait has read-only semantics while
  // a call to post has write semantics.
  static_assert(
      std::atomic<uint32_t>::is_always_lock_free,
      "Atomic operations need to be lock free for multi-process communication");
  mutable std::atomic<uint32_t> val_ = {0};
  const bool private_futex_ = false;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_INTERPROCESS_BINARY_FUTEX_H_
