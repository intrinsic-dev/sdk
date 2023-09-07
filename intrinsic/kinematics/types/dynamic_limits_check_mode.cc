// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/kinematics/types/dynamic_limits_check_mode.h"

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/kinematics/types/dynamic_limits_check_mode.pb.h"

namespace intrinsic {

intrinsic_proto::DynamicLimitsCheckMode ToProto(
    const DynamicLimitsCheckMode& dynamic_limits_check_mode) {
  switch (dynamic_limits_check_mode) {
    case DynamicLimitsCheckMode::kCheckJointAcceleration: {
      return intrinsic_proto::DynamicLimitsCheckMode::
          DYNAMIC_LIMITS_CHECK_MODE_CHECK_JOINT_ACCELERATION;
    }
    case DynamicLimitsCheckMode::kCheckNone: {
      return intrinsic_proto::DynamicLimitsCheckMode::
          DYNAMIC_LIMITS_CHECK_MODE_CHECK_NONE;
    }
    default: {
      return intrinsic_proto::DynamicLimitsCheckMode::
          DYNAMIC_LIMITS_CHECK_MODE_CHECK_JOINT_ACCELERATION;
    }
  }
}

absl::StatusOr<DynamicLimitsCheckMode> FromProto(
    const intrinsic_proto::DynamicLimitsCheckMode&
        dynamic_limits_check_mode_proto) {
  switch (dynamic_limits_check_mode_proto) {
    case intrinsic_proto::DYNAMIC_LIMITS_CHECK_MODE_TYPE_UNSPECIFIED: {
      // An UNSPECIFIED option is not available in the c++ enum class, thus this
      // value gets mapped to the default value `kCheckJointAcceleration`.
      return DynamicLimitsCheckMode::kCheckJointAcceleration;
    }
    case intrinsic_proto::DYNAMIC_LIMITS_CHECK_MODE_CHECK_JOINT_ACCELERATION: {
      return DynamicLimitsCheckMode::kCheckJointAcceleration;
    }
    case intrinsic_proto::DYNAMIC_LIMITS_CHECK_MODE_CHECK_NONE: {
      return DynamicLimitsCheckMode::kCheckNone;
    }
    default: {
      return absl::InvalidArgumentError(
          "Unknown type in DynamicLimitsCheckMode.");
    }
  }
}

}  // namespace intrinsic
