// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/proto/eigen_conversion.h"

#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/icon/proto/joint_space.pb.h"
#include "intrinsic/icon/proto/matrix.pb.h"

namespace intrinsic::icon {

intrinsic_proto::icon::JointVec ToJointVecProto(const eigenmath::VectorNd& v) {
  intrinsic_proto::icon::JointVec proto;
  details::ToRepeatedDouble(v, proto.mutable_joints());
  return proto;
}

intrinsic_proto::icon::JointStatePV ToJointStatePVProtoWithZeroVel(
    const eigenmath::VectorNd& v) {
  intrinsic_proto::icon::JointStatePV proto;
  details::ToRepeatedDouble(v, proto.mutable_position());

  eigenmath::VectorNd zero_vec = eigenmath::VectorNd::Constant(v.size(), 0.0);
  details::ToRepeatedDouble(zero_vec, proto.mutable_velocity());
  return proto;
}

absl::StatusOr<eigenmath::VectorNd> FromProto(
    const intrinsic_proto::icon::JointVec& proto) {
  return RepeatedDoubleToVectorNd(proto.joints());
}

intrinsic_proto::icon::Matrix6d ToProto(const eigenmath::Matrix6d& matrix) {
  intrinsic_proto::icon::Matrix6d proto;
  proto.mutable_data()->Resize(36, 0);
  for (int i = 0; i < 6; ++i) {
    for (int j = 0; j < 6; ++j) {
      proto.set_data((i * 6) + j, matrix(i, j));
    }
  }
  return proto;
}

absl::StatusOr<eigenmath::Matrix6d> FromProto(
    const intrinsic_proto::icon::Matrix6d& proto) {
  eigenmath::Matrix6d out;
  if (proto.data_size() != 36) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Cannot read Matrix6d from proto: expected data size of 36, got ",
        proto.data_size(), ": proto=", proto));
  }
  for (int i = 0; i < 6; ++i) {
    for (int j = 0; j < 6; ++j) {
      out(i, j) = proto.data((i * 6) + j);
    }
  }
  return out;
}

intrinsic_proto::icon::CartVec6 ToProto(const eigenmath::Vector6d& vector) {
  intrinsic_proto::icon::CartVec6 proto;
  proto.set_x(vector(0));
  proto.set_y(vector(1));
  proto.set_z(vector(2));
  proto.set_rx(vector(3));
  proto.set_ry(vector(4));
  proto.set_rz(vector(5));
  return proto;
}

eigenmath::Vector6d FromProto(const intrinsic_proto::icon::CartVec6& proto) {
  eigenmath::Vector6d vector;
  vector(0) = proto.x();
  vector(1) = proto.y();
  vector(2) = proto.z();
  vector(3) = proto.rx();
  vector(4) = proto.ry();
  vector(5) = proto.rz();
  return vector;
}

}  // namespace intrinsic::icon
