// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/kinematics/types/joint_limits_xd.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <string>

#include "absl/strings/str_cat.h"
#include "absl/strings/substitute.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/eigen_conversion.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

using icon::RepeatedDoubleToVectorXd;
using icon::VectorXdToRepeatedDouble;

namespace {
bool IsInfiniteVector(const eigenmath::VectorXd& vec) {
  return std::any_of(vec.begin(), vec.end(),
                     [](double v) { return std::isinf(v); });
}

}  // namespace

JointLimitsXd JointLimitsXd::Unlimited(size_t size) {
  JointLimitsXd limits;
  limits.SetSize(size);
  limits.SetUnlimited();
  return limits;
}

JointLimitsXd JointLimitsXd::Create(const JointLimits& joint_limits) {
  return JointLimitsXd{.min_position = joint_limits.min_position,
                       .max_position = joint_limits.max_position,
                       .max_velocity = joint_limits.max_velocity,
                       .max_acceleration = joint_limits.max_acceleration,
                       .max_jerk = joint_limits.max_jerk,
                       .max_torque = joint_limits.max_torque};
}

eigenmath::VectorXd::Index JointLimitsXd::size() const {
  return min_position.size();
}

bool JointLimitsXd::IsSizeConsistent() const {
  const eigenmath::VectorXd::Index size = this->size();
  return ((min_position.rows() == size) && (max_position.rows() == size) &&
          (max_velocity.rows() == size) && (max_acceleration.rows() == size) &&
          (max_jerk.rows() == size) && (max_torque.rows() == size));
}

void JointLimitsXd::SetSize(eigenmath::VectorXd::Index size) {
  min_position = eigenmath::VectorXd::Constant(size, 0.);
  max_position = eigenmath::VectorXd::Constant(size, 0.);
  max_velocity = eigenmath::VectorXd::Constant(size, 0.);
  max_acceleration = eigenmath::VectorXd::Constant(size, 0.);
  max_jerk = eigenmath::VectorXd::Constant(size, 0.);
  max_torque = eigenmath::VectorXd::Constant(size, 0.);
}

void JointLimitsXd::SetUnlimited() {
  min_position.setConstant(-std::numeric_limits<double>::infinity());
  max_position.setConstant(std::numeric_limits<double>::infinity());
  max_velocity.setConstant(std::numeric_limits<double>::infinity());
  max_acceleration.setConstant(std::numeric_limits<double>::infinity());
  max_jerk.setConstant(std::numeric_limits<double>::infinity());
  max_torque.setConstant(std::numeric_limits<double>::infinity());
}

bool JointLimitsXd::IsValid() const {
  if (!IsSizeConsistent()) {
    return false;
  }

  if (size() == 0) {
    return true;
  }

  return (max_position - min_position).minCoeff() >= 0 &&
         (max_velocity.array() >= 0).all() &&
         (max_acceleration.array() >= 0).all() &&
         (max_jerk.array() >= 0).all() && (max_torque.array() >= 0).all();
}

absl::StatusOr<JointLimitsXd> UpdateJointLimits(
    const JointLimitsXd& base,
    const intrinsic_proto::JointLimitsUpdate& update) {
  JointLimitsXd out = base;
  if (!update.min_position().values().empty()) {
    if (update.min_position().values_size() != base.min_position.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. min_position sizes are different. Base "
          "size: $0 Actual size: $1",
          base.min_position.size(), update.min_position().values_size()));
    }
    out.min_position = RepeatedDoubleToVectorXd(update.min_position().values());
  }
  if (!update.max_position().values().empty()) {
    if (update.max_position().values_size() != base.max_position.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_position sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_position.size(), update.max_position().values_size()));
    }
    out.max_position = RepeatedDoubleToVectorXd(update.max_position().values());
  }
  if (!update.max_velocity().values().empty()) {
    if (update.max_velocity().values_size() != base.max_velocity.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_velocity sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_velocity.size(), update.max_velocity().values_size()));
    }
    out.max_velocity = RepeatedDoubleToVectorXd(update.max_velocity().values());
  }
  if (!update.max_acceleration().values().empty()) {
    if (update.max_acceleration().values_size() !=
        base.max_acceleration.size()) {
      return absl::InvalidArgumentError(
          absl::Substitute("Cannot update joint limits. max_acceleration sizes "
                           "are different. Base size: $0 Actual size: $1",
                           base.max_acceleration.size(),
                           update.max_acceleration().values_size()));
    }

    out.max_acceleration =
        RepeatedDoubleToVectorXd(update.max_acceleration().values());
  }
  if (!update.max_jerk().values().empty()) {
    if (update.max_jerk().values_size() != base.max_jerk.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_jerk sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_jerk.size(), update.max_jerk().values_size()));
    }
    out.max_jerk = RepeatedDoubleToVectorXd(update.max_jerk().values());
  }
  if (!update.max_effort().values().empty()) {
    if (update.max_effort().values_size() != base.max_torque.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_effort sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_torque.size(), update.max_effort().values_size()));
    }
    out.max_torque = RepeatedDoubleToVectorXd(update.max_effort().values());
  }
  return out;
}

intrinsic_proto::JointLimits ToProto(const JointLimitsXd& limits) {
  intrinsic_proto::JointLimits limits_proto;
  VectorXdToRepeatedDouble(
      limits.min_position,
      limits_proto.mutable_min_position()->mutable_values());
  VectorXdToRepeatedDouble(
      limits.max_position,
      limits_proto.mutable_max_position()->mutable_values());
  if (!IsInfiniteVector(limits.max_velocity)) {
    VectorXdToRepeatedDouble(
        limits.max_velocity,
        limits_proto.mutable_max_velocity()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_acceleration)) {
    VectorXdToRepeatedDouble(
        limits.max_acceleration,
        limits_proto.mutable_max_acceleration()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_jerk)) {
    VectorXdToRepeatedDouble(limits.max_jerk,
                             limits_proto.mutable_max_jerk()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_torque)) {
    VectorXdToRepeatedDouble(
        limits.max_torque, limits_proto.mutable_max_effort()->mutable_values());
  }
  return limits_proto;
}

absl::StatusOr<JointLimitsXd> ToJointLimitsXd(
    const intrinsic_proto::JointLimits& limits_proto) {
  const eigenmath::VectorXd min_position =
      RepeatedDoubleToVectorXd(limits_proto.min_position().values());

  auto limits = JointLimitsXd::Unlimited(min_position.size());

  limits.min_position = min_position;
  limits.max_position =
      RepeatedDoubleToVectorXd(limits_proto.max_position().values());
  if (limits_proto.has_max_velocity()) {
    limits.max_velocity =
        RepeatedDoubleToVectorXd(limits_proto.max_velocity().values());
  }
  if (limits_proto.has_max_acceleration()) {
    limits.max_acceleration =
        RepeatedDoubleToVectorXd(limits_proto.max_acceleration().values());
  }
  if (limits_proto.has_max_jerk()) {
    limits.max_jerk =
        RepeatedDoubleToVectorXd(limits_proto.max_jerk().values());
  }
  if (limits_proto.has_max_effort()) {
    limits.max_torque =
        RepeatedDoubleToVectorXd(limits_proto.max_effort().values());
  }
  if (!limits.IsValid()) {
    return absl::InvalidArgumentError(
        absl::StrCat("Joint limits proto are invalid:\n", limits_proto));
  }
  return limits;
}

intrinsic_proto::JointLimitsUpdate ToJointLimitsUpdate(
    const JointLimitsXd& limits) {
  intrinsic_proto::JointLimitsUpdate limits_proto;
  VectorXdToRepeatedDouble(
      limits.min_position,
      limits_proto.mutable_min_position()->mutable_values());
  VectorXdToRepeatedDouble(
      limits.max_position,
      limits_proto.mutable_max_position()->mutable_values());
  if (!IsInfiniteVector(limits.max_velocity)) {
    VectorXdToRepeatedDouble(
        limits.max_velocity,
        limits_proto.mutable_max_velocity()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_acceleration)) {
    VectorXdToRepeatedDouble(
        limits.max_acceleration,
        limits_proto.mutable_max_acceleration()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_jerk)) {
    VectorXdToRepeatedDouble(limits.max_jerk,
                             limits_proto.mutable_max_jerk()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_torque)) {
    VectorXdToRepeatedDouble(
        limits.max_torque, limits_proto.mutable_max_effort()->mutable_values());
  }
  return limits_proto;
}

absl::StatusOr<JointLimits> ToJointLimits(const JointLimitsXd& limits) {
  if (limits.size() > eigenmath::VectorNd::MaxSizeAtCompileTime) {
    return absl::InvalidArgumentError(
        absl::StrCat("Can not construct JointLimits from JointLimitsXd, max "
                     "size exceeded. Got limits of size ",
                     limits.size(), ", but max size is ",
                     eigenmath::VectorNd::MaxSizeAtCompileTime, "."));
  }

  return JointLimits{.min_position = limits.min_position,
                     .max_position = limits.max_position,
                     .max_velocity = limits.max_velocity,
                     .max_acceleration = limits.max_acceleration,
                     .max_jerk = limits.max_jerk,
                     .max_torque = limits.max_torque};
}

std::string ToString(const JointLimitsXd& limits) {
  return absl::StrCat("min_p=", absl::StrJoin(limits.min_position, ","),
                      "\nmax_p=", absl::StrJoin(limits.max_position, ","),
                      "\nmax_v=", absl::StrJoin(limits.max_velocity, ","),
                      "\nmax_a=", absl::StrJoin(limits.max_acceleration, ","),
                      "\nmax_j=", absl::StrJoin(limits.max_jerk, ","),
                      "\nmax_t=", absl::StrJoin(limits.max_torque, ","));
}

}  // namespace intrinsic
