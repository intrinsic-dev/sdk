// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_INTERFACES_JOINT_LIMITS_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_JOINT_LIMITS_UTILS_H_

#include "flatbuffers/flatbuffers.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/interfaces/joint_limits_generated.h"
#include "intrinsic/kinematics/types/joint_limits.pb.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildJointLimits(uint32_t num_dof);

}  // namespace intrinsic_fbs

namespace intrinsic::icon {

// Parses a JointLimits protobuf into a JointLimits hardware interface handle.
// Returns kInvalidArgument if the number of joints in the non-empty protobuf
// fields are not equal to the ones in the flatbuffer handle. Expects all
// non-empty JointLimits proto fields to have the same size and each flatbuffer
// field to match that size.
absl::Status ParseProtoJointLimits(
    const intrinsic_proto::JointLimits& pb_limits,
    intrinsic::icon::MutableHardwareInterfaceHandle<intrinsic_fbs::JointLimits>&
        fb_limits);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_INTERFACES_JOINT_LIMITS_UTILS_H_
