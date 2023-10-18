// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/binary_futex.h"

#include <linux/futex.h>
#include <sys/syscall.h>

#include <atomic>

#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {
namespace {

inline int64_t futex(std::atomic<uint32_t> &uaddr, int futex_op, uint32_t val,
                     const struct timespec *timeout = nullptr,
                     uint32_t *uaddr2 = nullptr,
                     uint32_t val3 = 0) INTRINSIC_SUPPRESS_REALTIME_CHECK {
  // For the static analysis, we allow futex operations even though they can
  // be blocking, because the blocking behavior is usually intended.
  return syscall(SYS_futex, &uaddr, futex_op, val, timeout, uaddr2,
                 FUTEX_BITSET_MATCH_ANY);
}

RealtimeStatus Wait(std::atomic<uint32_t> &val, const timespec *ts) {
  const absl::Time start_time = absl::Now();
  while (true) {
    // If the value is what we expect, we can return.
    uint32_t one = 1;
    if (val.compare_exchange_strong(one, 0)) {
      return OkStatus();
    }

    // The value is not yet what we expect, let's wait for it.
    auto ret = futex(val, FUTEX_WAIT_BITSET | FUTEX_CLOCK_REALTIME, 0, ts);
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

BinaryFutex::BinaryFutex(bool posted) : val_(posted == true ? 1 : 0) {}
BinaryFutex::BinaryFutex(BinaryFutex &&other) : val_(other.val_.load()) {}
BinaryFutex &BinaryFutex::operator=(BinaryFutex &&other) {
  if (this != &other) {
    val_.store(other.val_.load());
  }
  return *this;
}

RealtimeStatus BinaryFutex::Post() {
  uint32_t zero = 0;
  if (val_.compare_exchange_strong(zero, 1)) {
    // One indicating that we wake up at most 1 other client.
    if (futex(val_, FUTEX_WAKE, 1) == -1) {
      return InternalError(strerror(errno));
    }
  }
  return OkStatus();
}

RealtimeStatus BinaryFutex::WaitUntil(absl::Time deadline) const {
  if (deadline < absl::Now()) {
    return DeadlineExceededError("Specified deadline is in the past");
  }
  if (deadline == absl::InfiniteFuture()) {
    return Wait(val_, nullptr);
  }
  auto ts = absl::ToTimespec(deadline);
  return Wait(val_, &ts);
}

RealtimeStatus BinaryFutex::WaitFor(absl::Duration timeout) const {
  return WaitUntil(absl::Now() + timeout);
}

uint32_t BinaryFutex::Value() const { return val_; }

}  // namespace intrinsic::icon
