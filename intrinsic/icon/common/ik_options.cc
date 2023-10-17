// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/common/ik_options.h"

#include <vector>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/eigen_conversion.h"
#include "intrinsic/icon/proto/ik_options.pb.h"

namespace intrinsic {
namespace icon {

IKOptions FromProto(const intrinsic_proto::icon::IKOptions& proto) {
  return IKOptions{
      .preferred_joint_positions =
          RepeatedDoubleToVectorXd(proto.preferred_joint_positions()),
      .preferred_joint_positions_weight =
          proto.preferred_joint_positions_weight(),
  };
}

intrinsic_proto::icon::IKOptions ToProto(const IKOptions& obj) {
  intrinsic_proto::icon::IKOptions proto;
  VectorXdToRepeatedDouble(obj.preferred_joint_positions,
                           proto.mutable_preferred_joint_positions());
  proto.set_preferred_joint_positions_weight(
      obj.preferred_joint_positions_weight);
  return proto;
}

}  // namespace icon
}  // namespace intrinsic
