// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/motion_planning/conversions.h"

#include <vector>

#include "intrinsic/util/eigen.h"

namespace intrinsic {

std::vector<eigenmath::VectorXd> ToVectorXds(
    const google::protobuf::RepeatedPtrField<intrinsic_proto::icon::JointVec>&
        vectors) {
  std::vector<eigenmath::VectorXd> out;
  out.reserve(vectors.size());
  for (const auto& v : vectors) {
    out.push_back(RepeatedDoubleToVectorXd(v.joints()));
  }
  return out;
}

void ToJointVecs(
    const std::vector<eigenmath::VectorXd>& path,
    google::protobuf::RepeatedPtrField<intrinsic_proto::icon::JointVec>*
        vectors) {
  vectors->Clear();
  vectors->Reserve(path.size());
  for (const auto& point : path) {
    auto* new_point_proto = vectors->Add();
    VectorXdToRepeatedDouble(point, new_point_proto->mutable_joints());
  }
}

}  // namespace intrinsic
