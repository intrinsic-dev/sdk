// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_COMMON_IK_OPTIONS_H_
#define INTRINSIC_ICON_COMMON_IK_OPTIONS_H_

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/ik_options.pb.h"

namespace intrinsic {
namespace icon {

// Options for Inverse Kinematics.
// This is used in nullspace redundancy resolution.
struct IKOptions {
  // Preferred joint position for nullspace redundancy resolution.
  eigenmath::VectorNd preferred_joint_positions;
  // Weight to give to preferred joint position.
  double preferred_joint_positions_weight;
};

intrinsic_proto::icon::IKOptions ToProto(const IKOptions& obj);
IKOptions FromProto(const intrinsic_proto::icon::IKOptions& proto);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_COMMON_IK_OPTIONS_H_
