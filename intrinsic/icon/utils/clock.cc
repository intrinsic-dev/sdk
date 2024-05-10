// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/clock.h"

#include <cstdio>
#include <cstring>
#include <ctime>
#include <memory>
#include <utility>

#include "absl/log/check.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/duration.h"
#include "intrinsic/icon/utils/log_internal.h"

namespace intrinsic {

static inline int64_t MonotonicNowNSec() {
  timespec ts;
  (void)clock_gettime(CLOCK_MONOTONIC, &ts);
  return ToInt64Nanoseconds(DurationFromTimespec(ts));
}

// ----------------------------------------------------------------------------

// A monotonic clock.
class MonotonicClock : public Clock::IClockDriver {
 public:
  MonotonicClock() = default;

  // Implement Clock::IClockDriver.
  Clock::time_point now() const override {
    return timeFromNSec(MonotonicNowNSec());
  }
};

// A monotonic clock with an offset.
class OffsetClock : public Clock::IClockDriver {
 public:
  OffsetClock(Duration offset) : offset_(offset) {}

  // Implement Clock::IClockDriver.
  Clock::time_point now() const override {
    return timeFromNSec(MonotonicNowNSec()) + offset_;
  }

 private:
  const Duration offset_;
};

// A monotonic clock that starts at zero.
class ZeroedClock : public OffsetClock {
 public:
  ZeroedClock() : OffsetClock(Nanoseconds(-MonotonicNowNSec())) {}
};

std::shared_ptr<Clock::IClockDriver>* Clock::clock_ = nullptr;
std::shared_ptr<Clock::IClockDriver>* Clock::default_clock_ = nullptr;

Clock::time_point Clock::Now() noexcept {
  Init();
  return (*clock_)->now();
}

void Clock::Init() INTRINSIC_SUPPRESS_REALTIME_CHECK {
  static bool once = InitInternalOnce();
  (void)once;  // Used only to enforce one-time initialization.
}

static void LoggerGetTimeFunction(int64_t* robot_timestamp_ns,
                                  int64_t* wall_timestamp_ns) {
  *robot_timestamp_ns = Clock::now_ns();
  struct timespec ts_wall;
  clock_gettime(CLOCK_REALTIME, &ts_wall);
  *wall_timestamp_ns =
      ts_wall.tv_nsec + static_cast<uint64_t>(ts_wall.tv_sec) * NSECS_PER_SEC;
}

bool Clock::InitInternalOnce() {
  CHECK_EQ(clock_, nullptr);  // only called once.
  default_clock_ = new std::shared_ptr<IClockDriver>;
  clock_ = new std::shared_ptr<IClockDriver>;
  *default_clock_ = std::make_shared<MonotonicClock>();
  *clock_ = *default_clock_;
  icon::GlobalLogContext::SetTimeFunction(&LoggerGetTimeFunction);
  return true;
}

void Clock::setClockImpl(std::shared_ptr<IClockDriver> clock) {
  Init();
  if (clock == nullptr) {
    *clock_ = *default_clock_;
  } else {
    *clock_ = std::move(clock);
  }
}

namespace {

// This ensures that Clock::Init() is called once at initialization time,
// pre-empting any raciness later on.
const auto kUnused = Clock::Now();

}  // namespace

namespace icon {

Time FindNextCycleEnd(Time now, Time end, Duration period) {
  CHECK_GT(period.count(), 0) << "Period must be greater than 0.";

  // If we haven't reached the end, return the next end.
  if (now < end) return end + period;

  // Calculate how many cycles we missed.
  auto missed_cycles = (now - end) / period;
  return end + period * (missed_cycles + 1);
}

}  // namespace icon
}  // namespace intrinsic
