// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/proto/cart_space_conversion.h"

#include <cstdlib>
#include <string>

#include "Eigen/Geometry"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/icon/proto/eigen_conversion.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"
#include "intrinsic/util/status/status_builder.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

namespace {
template <typename ProtoT, typename CartVectorT>
ProtoT CartVectorToProto(const CartVectorT& obj) {
  ProtoT out;
  out.set_x(obj.x());
  out.set_y(obj.y());
  out.set_z(obj.z());
  out.set_rx(obj.RX());
  out.set_ry(obj.RY());
  out.set_rz(obj.RZ());
  return out;
}

template <typename ProtoT, typename CartVectorT>
CartVectorT CartVectorFromProto(const ProtoT& proto) {
  CartVectorT out;
  out.x() = proto.x();
  out.y() = proto.y();
  out.z() = proto.z();
  out.RX() = proto.rx();
  out.RY() = proto.ry();
  out.RZ() = proto.rz();
  return out;
}
}  // namespace

intrinsic_proto::icon::Twist ToProto(const Twist& twist) {
  return CartVectorToProto<intrinsic_proto::icon::Twist, Twist>(twist);
}

Twist FromProto(const intrinsic_proto::icon::Twist& proto) {
  return CartVectorFromProto<intrinsic_proto::icon::Twist, Twist>(proto);
}

intrinsic_proto::icon::Acceleration ToProto(const Acceleration& acc) {
  return CartVectorToProto<intrinsic_proto::icon::Acceleration, Acceleration>(
      acc);
}

Acceleration FromProto(const intrinsic_proto::icon::Acceleration& proto) {
  return CartVectorFromProto<intrinsic_proto::icon::Acceleration, Acceleration>(
      proto);
}

intrinsic_proto::icon::Wrench ToProto(const Wrench& wrench) {
  return CartVectorToProto<intrinsic_proto::icon::Wrench, Wrench>(wrench);
}

Wrench FromProto(const intrinsic_proto::icon::Wrench& proto) {
  return CartVectorFromProto<intrinsic_proto::icon::Wrench, Wrench>(proto);
}

intrinsic_proto::icon::CartesianLimits ToProto(const CartesianLimits& limits) {
  intrinsic_proto::icon::CartesianLimits out;
  Vector3dToRepeatedDouble(limits.min_translational_position,
                           out.mutable_min_translational_position());
  Vector3dToRepeatedDouble(limits.max_translational_position,
                           out.mutable_max_translational_position());
  Vector3dToRepeatedDouble(limits.min_translational_velocity,
                           out.mutable_min_translational_velocity());
  Vector3dToRepeatedDouble(limits.max_translational_velocity,
                           out.mutable_max_translational_velocity());
  Vector3dToRepeatedDouble(limits.min_translational_acceleration,
                           out.mutable_min_translational_acceleration());
  Vector3dToRepeatedDouble(limits.max_translational_acceleration,
                           out.mutable_max_translational_acceleration());
  Vector3dToRepeatedDouble(limits.min_translational_jerk,
                           out.mutable_min_translational_jerk());
  Vector3dToRepeatedDouble(limits.max_translational_jerk,
                           out.mutable_max_translational_jerk());
  out.set_max_rotational_velocity(limits.max_rotational_velocity);
  out.set_max_rotational_acceleration(limits.max_rotational_acceleration);
  out.set_max_rotational_jerk(limits.max_rotational_jerk);
  return out;
}

absl::StatusOr<CartesianLimits> FromProto(
    const intrinsic_proto::icon::CartesianLimits& proto) {
  CartesianLimits out;
  INTR_ASSIGN_OR_RETURN(
      out.min_translational_position,
      RepeatedDoubleToVector3d(proto.min_translational_position()));
  INTR_ASSIGN_OR_RETURN(
      out.max_translational_position,
      RepeatedDoubleToVector3d(proto.max_translational_position()));
  INTR_ASSIGN_OR_RETURN(
      out.min_translational_velocity,
      RepeatedDoubleToVector3d(proto.min_translational_velocity()));
  INTR_ASSIGN_OR_RETURN(
      out.max_translational_velocity,
      RepeatedDoubleToVector3d(proto.max_translational_velocity()));
  INTR_ASSIGN_OR_RETURN(
      out.min_translational_acceleration,
      RepeatedDoubleToVector3d(proto.min_translational_acceleration()));
  INTR_ASSIGN_OR_RETURN(
      out.max_translational_acceleration,
      RepeatedDoubleToVector3d(proto.max_translational_acceleration()));
  INTR_ASSIGN_OR_RETURN(
      out.min_translational_jerk,
      RepeatedDoubleToVector3d(proto.min_translational_jerk()));
  INTR_ASSIGN_OR_RETURN(
      out.max_translational_jerk,
      RepeatedDoubleToVector3d(proto.max_translational_jerk()));
  out.max_rotational_velocity = proto.max_rotational_velocity();
  out.max_rotational_acceleration = proto.max_rotational_acceleration();
  out.max_rotational_jerk = proto.max_rotational_jerk();
  if (!out.IsValid()) {
    return absl::InvalidArgumentError(
        absl::StrCat("Cartesian limits are invalid: ", proto));
  }
  return out;
}

intrinsic_proto::icon::Transform ToProto(const Pose3d& pose) {
  intrinsic_proto::icon::Transform out;
  intrinsic_proto::icon::Point pos;
  pos.set_x(pose.translation().x());
  pos.set_y(pose.translation().y());
  pos.set_z(pose.translation().z());

  intrinsic_proto::icon::Rotation rot;
  rot.set_qx(pose.quaternion().x());
  rot.set_qy(pose.quaternion().y());
  rot.set_qz(pose.quaternion().z());
  rot.set_qw(pose.quaternion().w());

  *out.mutable_pos() = pos;
  *out.mutable_rot() = rot;
  return out;
}

absl::StatusOr<Pose3d> FromProto(
    const intrinsic_proto::icon::Transform& proto) {
  eigenmath::Quaterniond quat{proto.rot().qw(), proto.rot().qx(),
                              proto.rot().qy(), proto.rot().qz()};
  if (std::abs(quat.squaredNorm() - 1.0f) >=
      Eigen::NumTraits<double>::dummy_precision()) {
    return absl::InvalidArgumentError(
        absl::StrCat("Cannot deserialize control::Transform: quaternion is not "
                     "normalized; proto=",
                     proto));
  }
  return Pose3d(
      quat,
      eigenmath::Vector3d{proto.pos().x(), proto.pos().y(), proto.pos().z()},
      eigenmath::kDoNotNormalize);
}

}  // namespace intrinsic::icon
