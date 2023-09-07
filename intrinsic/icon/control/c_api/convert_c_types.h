// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_TYPES_H_
#define INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_TYPES_H_

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/c_api/c_types.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic::icon {

// These helpers convert back and forth between ICON C++ vocabulary types and
// their C API equivalents.
//
// Note that these functions do CHECKs to ensure that sizes are compatible and
// will crash if the input has (or claims to have) more values than the output
// type can handle. These checks are *not* exposed via (Realtime)Status return
// values because a static_assert in convert_c_types.cc ensures that the maximum
// size of C and C++ vectors is the same.
//
// If a user puts an invalid value into the `size` member of one of the C data
// structs, that's on them.

JointPositionCommand Convert(const XfaIconJointPositionCommand& in);
XfaIconJointPositionCommand Convert(const JointPositionCommand& in);

JointLimits Convert(const XfaIconJointLimits& in);
XfaIconJointLimits Convert(const JointLimits& in);

JointStateP Convert(const XfaIconJointStateP& in);
XfaIconJointStateP Convert(const JointStateP& in);

JointStateV Convert(const XfaIconJointStateV& in);
XfaIconJointStateV Convert(const JointStateV& in);

JointStateA Convert(const XfaIconJointStateA& in);
XfaIconJointStateA Convert(const JointStateA& in);

eigenmath::Quaterniond Convert(const XfaIconQuaternion& in);
XfaIconQuaternion Convert(const eigenmath::Quaterniond& in);

eigenmath::Vector3d Convert(const XfaIconPoint& in);
XfaIconPoint Convert(const eigenmath::Vector3d& in);

Pose3d Convert(const XfaIconPose3d& in);
XfaIconPose3d Convert(const Pose3d& in);

Wrench Convert(const XfaIconWrench& in);
XfaIconWrench Convert(const Wrench& in);

eigenmath::Matrix6Nd Convert(const XfaIconMatrix6Nd& in);
XfaIconMatrix6Nd Convert(const eigenmath::Matrix6Nd& in);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_TYPES_H_
