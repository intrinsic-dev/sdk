// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/math/proto_conversion.h"

#include <algorithm>
#include <cmath>
#include <limits>

#include "absl/strings/str_format.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic_proto {
namespace {
// 32 is 5 bits of mantissa error; should be adequate for common errors.
constexpr double kStdError = 32 * std::numeric_limits<double>::epsilon();

// Tests whether two values are close enough to each other to be considered
// equal. The purpose of AlmostEquals() is to avoid false positive error reports
// due to minute differences in floating point arithmetic (for example, due to a
// different compiler).
//
static bool AlmostEquals(const double x, const double y,
                         const double std_error = kStdError) {
  // If standard == says they are equal then we can return early.
  if (x == y) return true;

  const double abs_x = std::fabs(x);
  const double abs_y = std::fabs(y);

  if (abs_x <= std_error && abs_y <= std_error) return true;

  if (std::isinf(x) || std::isnan(x) || std::isinf(y) || std::isnan(y)) {
    return false;
  }

  const double relative_margin = std_error * std::max(abs_x, abs_y);
  const double max_error = std::max(std_error, relative_margin);

  if (x > y) {
    return (x - y) <= max_error;
  } else {
    return (y - x) <= max_error;
  }
}

}  // namespace

intrinsic::eigenmath::Vector3d FromProto(const Point& point) {
  return {point.x(), point.y(), point.z()};
}

intrinsic::eigenmath::Quaterniond FromProto(const Quaternion& quaternion) {
  // Eigen's Quaternion ctor takes parameters in the order {w, x, y, z}.
  return {quaternion.w(), quaternion.x(), quaternion.y(), quaternion.z()};
}

absl::StatusOr<intrinsic::Pose> FromProto(const Pose& pose) {
  intrinsic::eigenmath::Quaterniond quaternion = FromProto(pose.orientation());
  // We need to perform a soft-check in here, since otherwise, we might raise an
  // error status due to numeric errors introduced by the squared norm
  // computation.
  // Using exact float comparison, it is not necessarily true that
  //   Quaterniond::UnitRandom().norm() == 1.0
  if (const double squared_norm = quaternion.squaredNorm();
      !AlmostEquals(squared_norm, 1.0)) {
    const intrinsic::eigenmath::Quaterniond normalized_quat =
        quaternion.normalized();
    return absl::InvalidArgumentError(absl::StrFormat(
        "Failed to create Pose from proto which contains a "
        "non-unit quaternion with norm(quat) == %.17f . The normalized "
        "quaternion would be %.17f, %.17f, %.17f, %.17f",
        std::sqrt(squared_norm), normalized_quat.x(), normalized_quat.y(),
        normalized_quat.z(), normalized_quat.w()));
  }
  return intrinsic::Pose(quaternion, FromProto(pose.position()),
                         intrinsic::eigenmath::kDoNotNormalize);
}

absl::StatusOr<intrinsic::Pose> FromProtoNormalized(const Pose& pose) {
  intrinsic::eigenmath::Quaterniond quaternion = FromProto(pose.orientation());
  constexpr double kNormalizationError = 1e-3;
  const double squared_norm = quaternion.squaredNorm();
  // If we're already normalized to a reasonable degree, then simply don't
  // renormalize at all. This preserves the property that if we call
  // FromProtoNormalized(ToProto(pose)) that we get the same result back.
  if (AlmostEquals(squared_norm, 1.0)) {
    return intrinsic::Pose(quaternion, FromProto(pose.position()),
                           intrinsic::eigenmath::kDoNotNormalize);
  }

  const intrinsic::eigenmath::Quaterniond normalized_quat =
      quaternion.normalized();
  // We need to perform a soft-check in here, since otherwise, we might raise an
  // error status due to numeric errors introduced by the squared norm
  // computation or due to rounding. To enforce higher precision checks and not
  // allow normalization of the quaternion, please use FromProto directly.
  if (!AlmostEquals(squared_norm, 1.0, kNormalizationError)) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Failed to create Pose from proto which contains a "
        "non-unit quaternion with norm(quat) == %.6f . The normalized "
        "quaternion would be %.4f, %.4f, %.4f, %.4f. Provided quaternion %s",
        std::sqrt(squared_norm), normalized_quat.x(), normalized_quat.y(),
        normalized_quat.z(), normalized_quat.w(), pose.DebugString()));
  }
  return intrinsic::Pose(normalized_quat, FromProto(pose.position()),
                         intrinsic::eigenmath::kDoNotNormalize);
}

}  // namespace intrinsic_proto

namespace intrinsic {

intrinsic_proto::Pose ToProto(const Pose& pose) {
  intrinsic_proto::Pose proto_pose;
  *proto_pose.mutable_position() = ToProto(pose.translation());
  *proto_pose.mutable_orientation() = ToProto(pose.quaternion());
  return proto_pose;
}

intrinsic_proto::Point ToProto(const eigenmath::Vector3d& point) {
  intrinsic_proto::Point proto_point;
  proto_point.set_x(point.x());
  proto_point.set_y(point.y());
  proto_point.set_z(point.z());
  return proto_point;
}

intrinsic_proto::Quaternion ToProto(const eigenmath::Quaterniond& quaternion) {
  intrinsic_proto::Quaternion proto_quaternion;
  proto_quaternion.set_x(quaternion.x());
  proto_quaternion.set_y(quaternion.y());
  proto_quaternion.set_z(quaternion.z());
  proto_quaternion.set_w(quaternion.w());
  return proto_quaternion;
}

}  // namespace intrinsic
