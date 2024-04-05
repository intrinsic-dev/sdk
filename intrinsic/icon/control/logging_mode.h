// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_LOGGING_MODE_H_
#define INTRINSIC_ICON_CONTROL_LOGGING_MODE_H_

#include "intrinsic/icon/proto/logging_mode.pb.h"

namespace intrinsic::icon {

enum class LoggingMode : char {
  // Log at a throttled rate.
  kThrottled,
  // Log every cycle.
  kFullRate,
};

LoggingMode FromProto(const intrinsic_proto::icon::LoggingMode& proto);

intrinsic_proto::icon::LoggingMode ToProto(LoggingMode mode);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_LOGGING_MODE_H_
