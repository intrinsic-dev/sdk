// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_CLOCK_H_
#define INTRINSIC_ICON_UTILS_CLOCK_H_

#include <memory>
#include <ostream>
#include <ratio>

#include "intrinsic/icon/utils/clock_base.h"
#include "intrinsic/icon/utils/duration.h"

namespace intrinsic {

// Clock is mainly used to access the current time and sleep for a certain
// amount of time.
//
// Note: Do not assume that a Time is a unique value.  Different processes or
// threads may call Clock::Now() at the same time and return the same value.
//
// Examples:
//  ```C++
//      Time current_time = Clock::Now();
//  ```
//
//  ```C++
//      Time start = Clock::Now();
//      ...
//      Duration d = Clock::Now() - start;
//  ```
class Clock : public ClockBase<Clock> {
 public:
  // This clock never gets adjusted. needed by STL.
  static constexpr bool is_steady = true;

  /**
   * Returns the current time.
   *
   * This is a monotonically increasing clock.  That means it will not go
   * backwards.  However, it is possible that several calls in a row will all
   * produce the same value.  This is especially true when using the simulated
   * clock, where now() may return the same value for long periods of (cpu +
   * wall) time.
   *
   * @note In the simulation environment, simulated time is returned (as opposed
   * to the world's wall time). Simulated time may not be strictly monotonic.
   *
   * @warning This clock must not be used for profiling code, as it won't
   * produce meaningful values for that purpose in simulation.
   *
   * @return the current Time.
   */
  static inline time_point now() noexcept { return Now(); }
  static time_point Now() noexcept;

  // Helper function equivalent to toNsec<int64_t>(Clock::Now())
  static inline int64_t now_ns() noexcept {
    return std::chrono::duration_cast<
               std::chrono::duration<int64_t, std::nano>>(
               now().time_since_epoch())
        .count();
  }

  /*
   * No user serviceable parts below here
   * ------------------------------------
   */

  /**
   * An interface that provides access to the clock implementation.
   * All clock-related static methods of Clock funnel through
   * this interface.
   *
   * IClockDriver is used to replace the default clock, which is
   * typically used by unit tests and the simulator.
   *
   * @see setClockImpl
   */
  class IClockDriver {
   public:
    virtual ~IClockDriver() = default;

    /** @return the current time in nanosecond */
    virtual time_point now() const = 0;

    // IClockDriver cannot be copied
    IClockDriver(const IClockDriver&) = delete;
    IClockDriver& operator=(const IClockDriver&) = delete;

   protected:
    // We need the default ctor because we're hiding the copy-ctor
    IClockDriver() = default;
  };

  // Sets the Clock implementation.
  //
  // This is not thread safe and should generally only be called once when the
  // process is initialized.  The first time now() (or any other Clock method)
  // is called, this is called from Init (in a thread safe way) if the clock has
  // not been set before that.
  //
  // Some tests will call this for each subtest - this is safe if it is done
  // before the test spawns any threads.
  //
  // Calling this with a nullptr will use the default implementation. Unless
  // setDefaultClockImpl() has been called with something else, the default
  // clock is the system monotonic clock.
  static void setClockImpl(std::shared_ptr<IClockDriver> clock);

 private:
  static void Init();
  static bool InitInternalOnce();

  static std::shared_ptr<IClockDriver>* clock_;
  static std::shared_ptr<IClockDriver>* default_clock_;
};

using Time = Clock::time_point;

// Metafunction to return type=Clock given type Time.
template <>
struct TimepointToClock<Time> {
  using type = Clock;
};

/*
 * scalars to Time-since-epoch
 */
template <class T>
static inline Time timeFromSec(const T& d) {
  return Clock::FromSec(d);
}

template <class T>
static inline Time timeFromMSec(const T& d) {
  return Clock::FromMSec(d);
}

template <class T>
static inline Time timeFromUSec(const T& d) {
  return Clock::FromUSec(d);
}

template <class T>
static inline Time timeFromNSec(const T& d) {
  return Clock::FromNSec(d);
}

// Converts between an absolute deadline (Time) and a relative timeout
// (Duration).
//
// This is a simple add/subtract, except that some values are treated specially:
//
// TIMEOUT            INTERPRETATION  RESULTING DEADLINE
// -----------------  --------------  ----------------------
// kDurationZero      non blocking    kTimeZero
// kDurationInfinite  forever         kTimeInfinite
// negative           forever         kTimeInfinite
// positive           future          Clock::Now() + timeout
//
// DEADLINE           INTERPRETATION  RESULTING TIMEOUT
// -----------------  --------------  -----------------
// kTimeInfinite      forever         kDurationInfinite
// kTimeZero          non blocking    kDurationZero
// negative           non blocking    kDurationZero
// <= Clock::Now()    non blocking    kDurationZero
// >  Clock::Now()    future          deadline - Clock::Now()
//

// A time that, when used as a deadline, means "run forever" (no deadline).
// This will always compare greater than a valid intrinsic::Time (i.e. any value
// returned by intrinsic::Clock::now().
constexpr Time kTimeInfinite = Clock::Max();

// An invalid time value which intrinsic::Clock::now() will never return.
constexpr Time kTimeInvalid = Clock::Invalid();

// A time that is less than or equal to the current intrinsic::Clock()::now()
// time. Beware that intrinsic::Clock()::now() DOES return this value sometimes.
constexpr Time kTimeZero = Clock::Zero();

}  // namespace intrinsic

// This allows gunit to print out the values of Times.
namespace std {
namespace chrono {
static inline ostream& operator<<(ostream& os, const ::intrinsic::Time& t) {
  os << ::intrinsic::NanosecondString(t);
  return os;
}
}  // namespace chrono
}  // namespace std

#endif  // INTRINSIC_ICON_UTILS_CLOCK_H_
