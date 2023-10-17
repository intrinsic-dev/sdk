// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_CLOCK_BASE_H_
#define INTRINSIC_ICON_UTILS_CLOCK_BASE_H_

#include <chrono>  // NOLINT
#include <ctime>
#include <ratio>
#include <string>

#include "intrinsic/icon/utils/duration.h"

namespace intrinsic {

// A baseclass that implements many of the *Clock methods.
// The Clock template parameter should be the subclass.
//
// To create a MyClock subclass that meets the requirements of the std::chrono
// `Clock` concept:
//   - Create a subclass of ClockBase:
//        class MyClock : public ClockBase<MyClock> { ... };
//   - To indicate if the clock is monotonic or not add a public is_steady
//     member variable:
//        public:
//        static constexpr bool is_steady = <true-or-false>;
//   - Add a public Now() method that returns the time_point type:
//        static time_point Now() { return ...; }
//
// To make it work with all the blue:: methods/functions defined here, also
// define a specialization of TimepointToClock:
//
// ```C++
//   template <>
//   struct TimepointToClock<MyClock::time_point> {
//     using type = MyClock;
//   };
// ```
template <typename Clock>
class ClockBase {
 public:
  // types required for std::chrono `Clock`.
  using duration = Duration;
  using rep = duration::rep;
  using period = duration::period;
  using time_point = std::chrono::time_point<Clock, duration>;

  // Returns the current time.
  static time_point now() { return Clock::Now(); }

  // Constants.
  static constexpr time_point Max() { return time_point::max(); }
  static constexpr time_point Zero() { return FromNSec(0); }
  static constexpr time_point Invalid() { return FromNSec(-1); }

  // time_point conversions (time_point -> numeric timepoint)
  template <typename NumericT = int64_t>
  static constexpr NumericT ToNSec(const time_point& timepoint) {
    return std::chrono::duration_cast<
               std::chrono::duration<NumericT, std::nano>>(
               timepoint.time_since_epoch())
        .count();
  }

  template <typename NumericT = int64_t>
  static constexpr NumericT ToUSec(const time_point& timepoint) {
    return std::chrono::duration_cast<
               std::chrono::duration<NumericT, std::micro>>(
               timepoint.time_since_epoch())
        .count();
  }

  template <typename NumericT = int64_t>
  static constexpr NumericT ToMSec(const time_point& timepoint) {
    return std::chrono::duration_cast<
               std::chrono::duration<NumericT, std::milli>>(
               timepoint.time_since_epoch())
        .count();
  }

  template <typename NumericT = int64_t>
  static constexpr NumericT ToSec(const time_point& timepoint) {
    return std::chrono::duration_cast<
               std::chrono::duration<NumericT, std::ratio<1, 1>>>(
               timepoint.time_since_epoch())
        .count();
  }

  // time_point conversions (numeric timepoint -> time_point)
  template <typename NumericT>
  static constexpr time_point FromNSec(NumericT value) noexcept {
    return time_point(std::chrono::duration_cast<Duration>(
        std::chrono::duration<NumericT, std::nano>(value)));
  }

  template <typename NumericT>
  static constexpr time_point FromUSec(NumericT value) {
    return time_point(std::chrono::duration_cast<Duration>(
        std::chrono::duration<NumericT, std::micro>(value)));
  }

  template <typename NumericT>
  static constexpr time_point FromMSec(NumericT value) {
    return time_point(std::chrono::duration_cast<Duration>(
        std::chrono::duration<NumericT, std::milli>(value)));
  }

  template <typename NumericT>
  static constexpr time_point FromSec(NumericT value) {
    return time_point(std::chrono::duration_cast<Duration>(
        std::chrono::duration<NumericT>(value)));
  }

  // Convert to/from a timespec.
  static constexpr struct timespec ToTimespec(const time_point& timepoint) {
    struct timespec ts =
        ::intrinsic::ToTimespec(Nanoseconds(ToNSec(timepoint)));
    return ts;
  }
  static constexpr time_point FromTimespec(const struct timespec& ts) {
    return time_point(DurationFromTimespec(ts));
  }

  // Convert to/from a timeval.
  static constexpr struct timeval ToTimeval(const time_point& timepoint) {
    struct timeval ts = ::intrinsic::ToTimeval(Nanoseconds(ToNSec(timepoint)));
    return ts;
  }
  static constexpr time_point FromTimeval(const struct timeval& ts) {
    return time_point(DurationFromTimeval(ts));
  }

 protected:
  ClockBase() {}
};

// Metafunction returns type=Clock given Timepoint=Clock::time_point.
template <typename Timepoint>
struct TimepointToClock {};

template <typename T, typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
static constexpr T toSec(const Timepoint& t) {
  return Clock::template ToSec<T>(t);
}
template <typename T, typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
static constexpr T toMSec(const Timepoint& t) {
  return Clock::template ToMSec<T>(t);
}
template <typename T, typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
static constexpr T toUSec(const Timepoint& t) {
  return Clock::template ToUSec<T>(t);
}
template <typename T, typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
static constexpr T toNSec(const Timepoint& t) {
  return Clock::template ToNSec<T>(t);
}

// Convert Timepoint to String with format "%10d.%09d"
// "seconds.nanoseconds".
template <typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
std::string NanosecondString(Timepoint time) {
  return NanosecondString(Nanoseconds(toNSec<int64_t>(time)));
}

// Convert Timepoint to String with format "%10d.%06d"
// "seconds.microseconds". SystemTime is truncated, not rounded.
template <typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
std::string MicrosecondString(Timepoint time) {
  return MicrosecondString(Nanoseconds(toNSec<int64_t>(time)));
}

// Convert Timepoint to String with format "%10d.%03d"
// "seconds.milliseconds". SystemTime is truncated, not rounded.
template <typename Timepoint,
          typename Clock = typename TimepointToClock<Timepoint>::type>
std::string MillisecondString(Timepoint time) {
  return MillisecondString(Nanoseconds(toNSec<int64_t>(time)));
}

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_UTILS_CLOCK_BASE_H_
