// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_RELEASE_GRPC_TIME_SUPPORT_H_
#define INTRINSIC_ICON_RELEASE_GRPC_TIME_SUPPORT_H_

#include "absl/time/time.h"
#include "grpc/support/log.h"
#include "grpc/support/time.h"
#include "grpcpp/support/time.h"

namespace grpc {

template <>
class TimePoint<absl::Time> {
 public:
  explicit TimePoint(absl::Time time) : time_(TimeToGprTimespec(time)) {}

  gpr_timespec raw_time() const { return time_; }

 private:
  static gpr_timespec TimeToGprTimespec(absl::Time time);

  const gpr_timespec time_;
};

// Converts gpr timespec to absl::Time
absl::Time TimeFromGprTimespec(gpr_timespec time);

// Converts absl::Time to gpr timespec with clock type set to REALTIME
gpr_timespec GprTimeSpecFromTime(absl::Time time);

// Converts gpr timespec to absl::Duration. The gpr timespec clock type
// should be TIMESPAN.
absl::Duration DurationFromGprTimespec(gpr_timespec time);

// Converts absl::Duration to gpr timespec with clock type set to TIMESPAM
gpr_timespec GprTimeSpecFromDuration(absl::Duration duration);

// Creates an absolute-time deadline from now + dur.
gpr_timespec DeadlineFromDuration(absl::Duration dur);

}  // namespace grpc

#endif  // INTRINSIC_ICON_RELEASE_GRPC_TIME_SUPPORT_H_
