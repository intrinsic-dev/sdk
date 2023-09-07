// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_MOTION_PLANNING_CONVERSIONS_H_
#define INTRINSIC_MOTION_PLANNING_CONVERSIONS_H_

#include <vector>

#include "google/protobuf/repeated_field.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/joint_space.pb.h"

namespace intrinsic {

std::vector<eigenmath::VectorXd> ToVectorXds(
    const google::protobuf::RepeatedPtrField<intrinsic_proto::icon::JointVec>&
        vectors);
// Clears any data currently in vectors.
void ToJointVecs(
    const std::vector<eigenmath::VectorXd>& path,
    google::protobuf::RepeatedPtrField<intrinsic_proto::icon::JointVec>*
        vectors);

}  // namespace intrinsic

#endif  // INTRINSIC_MOTION_PLANNING_CONVERSIONS_H_
