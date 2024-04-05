// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/logging_mode.h"

#include "intrinsic/icon/proto/logging_mode.pb.h"

namespace intrinsic::icon {

LoggingMode FromProto(const intrinsic_proto::icon::LoggingMode& proto) {
  switch (proto) {
    case intrinsic_proto::icon::LoggingMode::LOGGING_MODE_FULL_RATE:
      return LoggingMode::kFullRate;
    case intrinsic_proto::icon::LoggingMode::LOGGING_MODE_UNSPECIFIED:
    case intrinsic_proto::icon::LoggingMode::LOGGING_MODE_THROTTLED:
    default:
      return LoggingMode::kThrottled;
  }
}

intrinsic_proto::icon::LoggingMode ToProto(LoggingMode logging_mode) {
  switch (logging_mode) {
    case LoggingMode::kFullRate:
      return intrinsic_proto::icon::LoggingMode::LOGGING_MODE_FULL_RATE;
    case LoggingMode::kThrottled:
    default:
      return intrinsic_proto::icon::LoggingMode::LOGGING_MODE_THROTTLED;
  }
}

}  // namespace intrinsic::icon
