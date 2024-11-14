// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/binary_futex.h"

#include <linux/futex.h>
#include <sys/syscall.h>

#include <atomic>
#include <cerrno>
#include <climits>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <optional>

#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {
namespace {

inline int64_t futex(std::atomic<uint32_t> *uaddr, int futex_op, uint32_t val,
                     bool private_futex,
                     const struct timespec *timeout = nullptr,
                     uint32_t *uaddr2 = nullptr,
                     uint32_t val3 = 0) INTRINSIC_SUPPRESS_REALTIME_CHECK {
  // For the static analysis, we allow futex operations even though they can
  // be blocking, because the blocking behavior is usually intended.

  if (private_futex) {
    // This option bit can be employed with all futex operations. It tells the
    // kernel that the futex is process-private and not shared with another
    // process (i.e., it is being used for synchronization only between threads
    // of the same process). This allows the kernel to make some
    // additional performance optimizations.
    futex_op |= FUTEX_PRIVATE_FLAG;
  }
  return syscall(SYS_futex, uaddr, futex_op, val, timeout, uaddr2,
                 FUTEX_BITSET_MATCH_ANY);
}

// Atomically reads from `val` and sets `val` to kReady *if* it was kPosted.
//
// Returns the value of `val` before the reset.
uint32_t TryWait(std::atomic<uint32_t> &val) {
  uint32_t expected = BinaryFutex::kPosted;
  // If `val != expected`, then this writes the _actual_ value of `val` into
  // `expected`.
  (void)val.compare_exchange_strong(expected, BinaryFutex::kReady);
  return expected;
}

RealtimeStatus Wait(std::atomic<uint32_t> &val, const timespec *ts,
                    bool private_futex) {
  const absl::Time start_time = absl::Now();
  while (true) {
    {
      uint32_t value = TryWait(val);
      switch (value) {
        case BinaryFutex::kReady:
          break;
        case BinaryFutex::kClosed:
          return AbortedError("BinaryFutex is closed, aborting Wait()");
        case BinaryFutex::kPosted:
          return OkStatus();
        default:
          return InternalError(RealtimeStatus::StrCat(
              "BinaryFutex took unexpected value: ", value));
      }
    }

    // The value is not yet what we expect, but still kReady. Let's wait for it
    // to change. FUTEX_WAIT_BITSET sleeps for as long as the value is still
    // equal to kReady.
    auto ret = futex(&val, FUTEX_WAIT_BITSET | FUTEX_CLOCK_REALTIME,
                     BinaryFutex::kReady, private_futex, ts);
    if (ret == -1 && errno == ETIMEDOUT) {
      return DeadlineExceededError(RealtimeStatus::StrCat(
          "Timeout after ",
          absl::ToDoubleMilliseconds(absl::Now() - start_time), " ms"));
    }
    // If we have an EAGAIN, we woke up because another thread changed the
    // underlying value and we can retry decrementing the atomic value.
    // If we have EINTR, we woke up from an external signal. We've encountered
    // various SIGPROF when running on forge and decided to ignore these and
    // retry sleeping. If we have any other error message, that means we have an
    // actual error.
    if (ret == -1 && errno != EAGAIN && errno != EINTR) {
      return InternalError(strerror(errno));
    }
  }
}

}  // namespace

BinaryFutex::BinaryFutex(bool posted, bool private_futex)
    : val_(posted == true ? BinaryFutex::kPosted : BinaryFutex::kReady),
      private_futex_(private_futex) {}
BinaryFutex::BinaryFutex(BinaryFutex &&other) : val_(other.val_.load()) {}
BinaryFutex &BinaryFutex::operator=(BinaryFutex &&other) {
  if (this != &other) {
    val_.store(other.val_.load());
  }
  return *this;
}

BinaryFutex::~BinaryFutex() { Close(); }

RealtimeStatus BinaryFutex::Post() {
  uint32_t expected = BinaryFutex::kReady;
  // We need to make a copy of the private_futex_ member variable. Otherwise,
  // we might end up with a data race if the thread destructing the futex
  // reads `val_` between the `compare_exchange_strong` and the
  // `futex` call.
  const bool private_futex = private_futex_;
  // Take the address before, since the class instance could be destroyed before
  // `futex()` is called.
  std::atomic<uint32_t> *val_addr = &val_;
  if (val_.compare_exchange_strong(expected, BinaryFutex::kPosted)) {
    // `futex` could fail with EFAULT, if `val_addr` is not a valid
    // user-space address anymore. This can happen if another thread destroyed
    // the BinaryFutex between the previous line and this one. Therefore, we
    // ignore the return value here. Another error value should only be EINVAL,
    // which should never happen here
    // ("EINVAL: The kernel detected an inconsistency between the user-space
    // state at uaddr and the kernel state—that is, it detected a waiter which
    // waits in FUTEX_LOCK_PI or FUTEX_LOCK_PI2 on uaddr.").
    //
    // One indicating that we wake up at most 1 other client.
    futex(val_addr, FUTEX_WAKE, 1, private_futex);
  } else if (expected == BinaryFutex::kClosed) {
    // When compare_exchange_strong returns false, it writes the current value
    // of the atomic into `expected`. We can check this to see if the
    // BinaryFutex is closed.
    return AbortedError("BinaryFutex is closed, aborting Post()");
  }
  return OkStatus();
}

RealtimeStatus BinaryFutex::WaitUntil(absl::Time deadline) const {
  if (deadline == absl::InfiniteFuture()) {
    return Wait(val_, nullptr, private_futex_);
  }
  auto ts = absl::ToTimespec(deadline);
  return Wait(val_, &ts, private_futex_);
}

RealtimeStatus BinaryFutex::WaitFor(absl::Duration timeout) const {
  return WaitUntil(absl::Now() + timeout);
}

std::optional<bool> BinaryFutex::TryWait() const {
  switch (icon::TryWait(val_)) {
    case BinaryFutex::kReady:
      return false;
    case BinaryFutex::kPosted:
      return true;
    case BinaryFutex::kClosed:
    default:
      return std::nullopt;
  }
}

uint32_t BinaryFutex::Value() const { return val_; }

void BinaryFutex::Close() {
  // We need to make a copy of the private_futex_ member variable. Otherwise,
  // we might end up with a data race if the thread destructing the futex
  // reads `val_` between the `compare_exchange_strong` and the
  // `futex` call.
  const bool private_futex = private_futex_;
  // Take the address before, since the class instance could be destroyed before
  // `futex()` is called.
  std::atomic<uint32_t> *val_addr = &val_;
  // Only signal waiters if the value changed (i.e. if it *wasn't already*
  // BinaryFutex::kClosed).
  if (val_.exchange(BinaryFutex::kClosed) != BinaryFutex::kClosed) {
    // `futex` could fail with EFAULT, if `val_addr` is not a valid
    // user-space address anymore. This can happen if another thread destroyed
    // the BinaryFutex between the previous line and this one. Therefore, we
    // ignore the return value here. Another error value should only be EINVAL,
    // which should never happen here
    // ("EINVAL: The kernel detected an inconsistency between the user-space
    // state at uaddr and the kernel state—that is, it detected a waiter which
    // waits in FUTEX_LOCK_PI or FUTEX_LOCK_PI2 on uaddr.").
    //
    // INT_MAX indicates that we wake up *all* waiters. We don't do this in
    // `Post()`, because waking an unknown number of waiters could take unbound
    // time and compromise realtime correctness, but since `Close()` happens on
    // shutdown, we're not worried about that here.
    futex(val_addr, FUTEX_WAKE, INT_MAX, private_futex);
  }
}

}  // namespace intrinsic::icon
