// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_DURATION_H_
#define INTRINSIC_ICON_UTILS_DURATION_H_

#include <chrono>  // NOLINT
#include <cinttypes>
#include <ctime>
#include <ostream>
#include <ratio>
#include <string>
#include <type_traits>

#include "absl/base/attributes.h"

namespace intrinsic {

using Duration = std::chrono::nanoseconds;

/* Constants */
static constexpr int64_t NSECS_PER_SEC = 1000000000;
static constexpr int64_t NSECS_PER_MSEC = 1000000;
static constexpr int64_t NSECS_PER_USEC = 1000;

static constexpr int64_t USECS_PER_SEC = 1000000;
static constexpr int64_t USECS_PER_MSEC = 1000;

static constexpr int64_t MSECS_PER_SEC = 1000;

constexpr Duration InfiniteDuration() { return Duration::max(); }

constexpr Duration ZeroDuration() { return Duration::zero(); }

namespace internal {
/*
 * Generic Duration to scalars
 */
template <class T>
static inline constexpr T toSec(const Duration& d) {
  return std::chrono::duration_cast<std::chrono::duration<T, std::ratio<1, 1>>>(
             d)
      .count();
}

template <class T>
static inline constexpr T toMSec(const Duration& d) {
  return std::chrono::duration_cast<std::chrono::duration<T, std::milli>>(d)
      .count();
}

template <class T>
static inline constexpr T toUSec(const Duration& d) {
  return std::chrono::duration_cast<std::chrono::duration<T, std::micro>>(d)
      .count();
}

template <class T>
static inline constexpr T toNSec(const Duration& d) {
  return std::chrono::duration_cast<std::chrono::duration<T, std::nano>>(d)
      .count();
}
}  // namespace internal

constexpr int64_t ToInt64Seconds(Duration d) {
  return internal::toSec<int64_t>(d);
}
constexpr int64_t ToInt64Milliseconds(Duration d) {
  return internal::toMSec<int64_t>(d);
}
constexpr int64_t ToInt64Microseconds(Duration d) {
  return internal::toUSec<int64_t>(d);
}
constexpr int64_t ToInt64Nanoseconds(Duration d) {
  return internal::toNSec<int64_t>(d);
}

constexpr double ToDoubleSeconds(Duration d) {
  return internal::toSec<double>(d);
}
constexpr double ToDoubleMilliseconds(Duration d) {
  return internal::toMSec<double>(d);
}
constexpr double ToDoubleMicroseconds(Duration d) {
  return internal::toUSec<double>(d);
}
constexpr double ToDoubleNanoseconds(Duration d) {
  return internal::toNSec<double>(d);
}

static inline timespec ToTimespec(Duration d) {
  struct timespec ts;
  if (d >= ZeroDuration()) {
    int64_t tmp = ToInt64Nanoseconds(d);
    ts.tv_sec = static_cast<time_t>(tmp / NSECS_PER_SEC);
    ts.tv_nsec = static_cast<long>(tmp % NSECS_PER_SEC);  // NOLINT
  } else {
    int64_t tmp = ToInt64Nanoseconds(-d);
    ts.tv_sec = -static_cast<time_t>(tmp / NSECS_PER_SEC);
    ts.tv_nsec = static_cast<long>(tmp % NSECS_PER_SEC);  // NOLINT
    if (ts.tv_nsec != 0) {
      ts.tv_nsec = NSECS_PER_SEC - ts.tv_nsec;
      ts.tv_sec--;
    }
  }
  return ts;
}

static inline timeval ToTimeval(Duration d) {
  struct timeval ts;
  if (d >= ZeroDuration()) {
    int64_t tmp = ToInt64Microseconds(d);
    ts.tv_sec = static_cast<time_t>(tmp / USECS_PER_SEC);
    ts.tv_usec = static_cast<long>(tmp % USECS_PER_SEC);  // NOLINT
  } else {
    int64_t tmp = ToInt64Microseconds(-d);
    ts.tv_sec = -static_cast<time_t>(tmp / USECS_PER_SEC);
    ts.tv_usec = static_cast<long>(tmp % USECS_PER_SEC);  // NOLINT
    if (ts.tv_usec != 0) {
      ts.tv_usec = USECS_PER_SEC - ts.tv_usec;
      ts.tv_sec--;
    }
  }
  return ts;
}

/*
 * scalars to Duration
 */
template <class T>
constexpr Duration Seconds(T n) {
  return std::chrono::duration_cast<Duration>(std::chrono::duration<T>(n));
}
template <class T>
constexpr Duration Milliseconds(T n) {
  return std::chrono::duration_cast<Duration>(
      std::chrono::duration<T, std::milli>(n));
}
template <class T>
constexpr Duration Microseconds(T n) {
  return std::chrono::duration_cast<Duration>(
      std::chrono::duration<T, std::micro>(n));
}
template <class T>
constexpr Duration Nanoseconds(T n) {
  return std::chrono::duration_cast<Duration>(
      std::chrono::duration<T, std::nano>(n));
}

template <class T, class U>
static inline constexpr T FromNSecToSec(const U& nsec) {
  return std::chrono::duration_cast<std::chrono::duration<T>>(
             std::chrono::duration<T, std::nano>(nsec))
      .count();
}

template <class T, class U>
static inline constexpr T FromSecToNSec(const U& sec) {
  return std::chrono::duration_cast<std::chrono::duration<T, std::nano>>(
             std::chrono::duration<U>(sec))
      .count();
}

/*
 * Duration to misc
 */

template <class T>
static inline constexpr T toHertz(const Duration& period) {
  return static_cast<T>(1 / ToDoubleSeconds(period));
}

/*
 * misc to Duration
 */
template <typename T, typename std::enable_if<std::is_integral<T>::value,
                                              T>::type* = nullptr>
static inline constexpr Duration fromHz(const T& hz) {
  return std::chrono::duration_cast<Duration>(std::chrono::seconds(1)) / hz;
}

template <typename T, typename std::enable_if<std::is_floating_point<T>::value,
                                              T>::type* = nullptr>
static inline constexpr Duration fromHz(const T& hz) {
  return Nanoseconds(static_cast<int64_t>(NSECS_PER_SEC / hz));
}

static inline constexpr Duration DurationFromTimespec(timespec ts) {
  return std::chrono::duration_cast<Duration>(
      std::chrono::seconds(ts.tv_sec) + std::chrono::nanoseconds(ts.tv_nsec));
}

static inline constexpr Duration DurationFromTimeval(timeval ts) {
  return std::chrono::duration_cast<Duration>(
      std::chrono::seconds(ts.tv_sec) + std::chrono::microseconds(ts.tv_usec));
}

// Convert Duration to string with format "%10d.%09d" "seconds.nanoseconds".
std::string NanosecondString(Duration duration);

// Convert Time to string with format "%10d.%06d" "seconds.microseconds".
// Duration is truncated towards zero, not rounded.
// If duration is negative then the - sign appears even if the truncated value
// is zero.
std::string MicrosecondString(Duration duration);

// Convert Time to string with format "%10d.%03d" "seconds.milliseconds".
// Duration is truncated towards zero, not rounded.
// If duration is negative then the - sign appears even if the truncated value
// is zero.
std::string MillisecondString(Duration duration);

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_UTILS_DURATION_H_
