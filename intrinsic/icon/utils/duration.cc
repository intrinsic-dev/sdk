// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/utils/duration.h"

#include <cinttypes>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>

namespace intrinsic {

// Returns a string of at least min_width characters containing duration.
// divisor is the value to divide nsec by to get precision digits.
// precision is the number of digits to the right of the decimal place.
// The negative sign is included if nsec is negative, even if the truncated
// value is 0.
template <int64_t kDivisor, int kPrecision, int kMinWidth>
static std::string DurationString(const Duration duration) {
  constexpr int kStart = kMinWidth - kPrecision;
  static_assert(kStart > 0, "Start must be greater than zero.");

  char buf[32];
  static_assert(sizeof(buf) > kMinWidth, "Buffer is not large enough.");
  int64_t duration_nsec = ToInt64Nanoseconds(duration);
  bool neg = duration_nsec < 0;
  int64_t abs_duration_nsec = std::abs(duration_nsec);
  memset(buf, ' ', kStart);
  int len =
      snprintf(buf + kStart, sizeof(buf) - kStart, "%" PRIu64 ".%0*" PRIu64,
               abs_duration_nsec / NSECS_PER_SEC, kPrecision,
               (abs_duration_nsec % NSECS_PER_SEC) / kDivisor);
  int end = kStart + len;
  if (neg) {
    len++;
    buf[end - len] = '-';
  }
  if (len < kMinWidth) {
    len = kMinWidth;
  }
  return std::string(buf + end - len, len);
}

std::string NanosecondString(Duration duration) {
  return DurationString<1, 9, 10 + 1 + 9>(duration);
}

std::string MicrosecondString(Duration duration) {
  return DurationString<NSECS_PER_USEC, 6, 10 + 1 + 6>(duration);
}

std::string MillisecondString(Duration duration) {
  return DurationString<NSECS_PER_MSEC, 3, 10 + 1 + 3>(duration);
}

}  // namespace intrinsic
