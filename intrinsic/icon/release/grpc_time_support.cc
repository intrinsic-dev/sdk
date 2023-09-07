// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/release/grpc_time_support.h"

#include "absl/time/time.h"
#include "grpc/support/log.h"
#include "grpc/support/time.h"
#include "grpcpp/support/time.h"

namespace grpc {

gpr_timespec TimePoint<absl::Time>::TimeToGprTimespec(absl::Time time) {
  if (time == absl::InfiniteFuture()) {
    return gpr_inf_future(GPR_CLOCK_REALTIME);
  }
  if (time == absl::InfinitePast()) {
    return gpr_inf_past(GPR_CLOCK_REALTIME);
  }

  gpr_timespec spec;
  timespec t = absl::ToTimespec(time);
  spec.tv_sec = t.tv_sec;
  spec.tv_nsec = static_cast<int32_t>(t.tv_nsec);
  spec.clock_type = GPR_CLOCK_REALTIME;
  return spec;
}

// Converts gpr timespec to absl::Time
absl::Time TimeFromGprTimespec(gpr_timespec time) {
  if (!gpr_time_cmp(time, gpr_inf_future(time.clock_type))) {
    return absl::InfiniteFuture();
  }
  if (!gpr_time_cmp(time, gpr_inf_past(time.clock_type))) {
    return absl::InfinitePast();
  }
  time = gpr_convert_clock_type(time, GPR_CLOCK_REALTIME);
  timespec ts;
  ts.tv_sec = static_cast<decltype(ts.tv_sec)>(time.tv_sec);
  ts.tv_nsec = static_cast<decltype(ts.tv_nsec)>(time.tv_nsec);
  return absl::TimeFromTimespec(ts);
}

// Converts absl::Time to gpr timespec with clock type set to REALTIME
gpr_timespec GprTimeSpecFromTime(absl::Time time) {
  TimePoint<absl::Time> at(time);
  return at.raw_time();
}

// Converts gpr timespec to absl::Duration. The gpr timespec clock type
// should be TIMESPAN.
absl::Duration DurationFromGprTimespec(gpr_timespec time) {
  GPR_ASSERT(time.clock_type == GPR_TIMESPAN);
  timespec ts;
  ts.tv_sec = static_cast<decltype(ts.tv_sec)>(time.tv_sec);
  ts.tv_nsec = static_cast<decltype(ts.tv_nsec)>(time.tv_nsec);
  return absl::DurationFromTimespec(ts);
}

// Converts absl::Duration to gpr timespec with clock type set to TIMESPAM
gpr_timespec GprTimeSpecFromDuration(absl::Duration duration) {
  if (absl::time_internal::IsInfiniteDuration(duration)) {
    if (duration > absl::ZeroDuration()) {
      return gpr_inf_future(GPR_TIMESPAN);
    } else {
      return gpr_inf_past(GPR_TIMESPAN);
    }
  }
  gpr_timespec gpr_ts;
  timespec ts = absl::ToTimespec(duration);
  gpr_ts.tv_sec = static_cast<decltype(gpr_ts.tv_sec)>(ts.tv_sec);
  gpr_ts.tv_nsec = static_cast<decltype(gpr_ts.tv_nsec)>(ts.tv_nsec);
  gpr_ts.clock_type = GPR_TIMESPAN;
  return gpr_ts;
}

// Creates an absolute-time deadline from now + dur.
gpr_timespec DeadlineFromDuration(absl::Duration dur) {
  if (absl::time_internal::IsInfiniteDuration(dur)) {
    if (dur > absl::ZeroDuration()) {
      return gpr_inf_future(GPR_CLOCK_MONOTONIC);
    } else {
      return gpr_inf_past(GPR_CLOCK_MONOTONIC);
    }
  }

  timespec t = absl::ToTimespec(dur);
  gpr_timespec span;
  span.tv_sec = t.tv_sec;
  span.tv_nsec = static_cast<int32_t>(t.tv_nsec);
  span.clock_type = GPR_TIMESPAN;
  return gpr_time_add(gpr_now(GPR_CLOCK_MONOTONIC), span);
}

}  // namespace grpc
