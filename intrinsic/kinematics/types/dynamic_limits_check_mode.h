// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_KINEMATICS_TYPES_DYNAMIC_LIMITS_CHECK_MODE_H_
#define INTRINSIC_KINEMATICS_TYPES_DYNAMIC_LIMITS_CHECK_MODE_H_

#include <cstdint>

#include "absl/status/statusor.h"
#include "intrinsic/kinematics/types/dynamic_limits_check_mode.pb.h"

namespace intrinsic {

// Enum with available limits types to be checked for second order variables
// such as joint accelerations or joint torques. The default behavior is to
// check joint accelerations `kCheckJointAcceleration`, but can be
// skipped with `kCheckNone`.
enum class DynamicLimitsCheckMode : int8_t {
  kCheckJointAcceleration,  // Checks joint acceleration limits.
  kCheckNone,  // No checks for second order variables such as torques or
               // joint accelerations limits.
};

intrinsic_proto::DynamicLimitsCheckMode ToProto(
    const DynamicLimitsCheckMode& dynamic_limits_check_mode);

// Maps a proto DynamicLimitsCheckMode to its equivalent enum class. As the
// proto has an additional UNSPECIFIED field compared to the c++ enum class,
// this one gets mapped to the default value of `kCheckJointAcceleration`.
// Returns an error if the input type is not known.
absl::StatusOr<DynamicLimitsCheckMode> FromProto(
    const intrinsic_proto::DynamicLimitsCheckMode&
        dynamic_limits_check_mode_proto);

}  // namespace intrinsic

#endif  // INTRINSIC_KINEMATICS_TYPES_DYNAMIC_LIMITS_CHECK_MODE_H_
