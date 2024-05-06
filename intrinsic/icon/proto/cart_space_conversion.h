// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_PROTO_CART_SPACE_CONVERSION_H_
#define INTRINSIC_ICON_PROTO_CART_SPACE_CONVERSION_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/icon/proto/cart_space.pb.h"
#include "intrinsic/kinematics/types/cartesian_limits.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic::icon {

// Converts a Twist to a proto::Twist proto.
intrinsic_proto::icon::Twist ToProto(const Twist& twist);

// Converts a proto::Twist proto to a Twist.
Twist FromProto(const intrinsic_proto::icon::Twist& proto);

// Converts an Acceleration to a proto::Acceleration proto.
intrinsic_proto::icon::Acceleration ToProto(const Acceleration& acc);

// Converts a proto::Acceleration proto to an Acceleration.
Acceleration FromProto(const intrinsic_proto::icon::Acceleration& proto);

// Converts a Wrench to a proto::Wrench proto.
intrinsic_proto::icon::Wrench ToProto(const Wrench& wrench);

// Converts a proto::Wrench proto to a Wrench.
Wrench FromProto(const intrinsic_proto::icon::Wrench& proto);

// Converts CartesianLimits to a proto::CartesianLimits proto.
intrinsic_proto::icon::CartesianLimits ToProto(const CartesianLimits& limits);

// Converts a proto::CartesianLimits proto to a CartesianLimits.
//
// If any of the limit vectors have size other than 3, an InvalidArgumentError
// is returned.
absl::StatusOr<CartesianLimits> FromProto(
    const intrinsic_proto::icon::CartesianLimits& proto);

// Converts a Pose3d to a proto::Transform proto.
//
// `pose` is converted as-is. If it has a non-normalized quaternion, then the
// conversion will still succeed, but `FromProto(ToProto(pose)` will fail.
intrinsic_proto::icon::Transform ToProto(const Pose3d& pose);

// Converts a proto::Transform proto to a Pose3d. Returns
// InvalidArgumentError if `rot` is not normalized.
absl::StatusOr<Pose3d> FromProto(const intrinsic_proto::icon::Transform& proto);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_PROTO_CART_SPACE_CONVERSION_H_
