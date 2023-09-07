// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/kinematics/types/joint_limits.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

#include "absl/strings/substitute.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/proto/eigen_conversion.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"

namespace intrinsic {

icon::RealtimeStatusOr<JointLimits> JointLimits::Unlimited(size_t size) {
  JointLimits limits;
  INTRINSIC_RT_RETURN_IF_ERROR(limits.SetSize(size));
  limits.SetUnlimited();
  return limits;
}

eigenmath::VectorXd::Index JointLimits::size() const {
  return min_position.size();
}

bool JointLimits::IsSizeConsistent() const {
  const eigenmath::VectorXd::Index size = this->size();
  return ((min_position.rows() == size) && (max_position.rows() == size) &&
          (max_velocity.rows() == size) && (max_acceleration.rows() == size) &&
          (max_jerk.rows() == size) && (max_torque.rows() == size));
}

icon::RealtimeStatus JointLimits::SetSize(eigenmath::VectorXd::Index size) {
  if (size > kMaxSize) {
    return icon::InvalidArgumentError(icon::RealtimeStatus::StrCat(
        "size=", size, " exceeds max size=", kMaxSize));
  }
  min_position = eigenmath::VectorNd::Constant(size, 0.);
  max_position = eigenmath::VectorNd::Constant(size, 0.);
  max_velocity = eigenmath::VectorNd::Constant(size, 0.);
  max_acceleration = eigenmath::VectorNd::Constant(size, 0.);
  max_jerk = eigenmath::VectorNd::Constant(size, 0.);
  max_torque = eigenmath::VectorNd::Constant(size, 0.);
  return icon::OkStatus();
}

void JointLimits::SetUnlimited() {
  min_position.setConstant(-std::numeric_limits<double>::infinity());
  max_position.setConstant(std::numeric_limits<double>::infinity());
  max_velocity.setConstant(std::numeric_limits<double>::infinity());
  max_acceleration.setConstant(std::numeric_limits<double>::infinity());
  max_jerk.setConstant(std::numeric_limits<double>::infinity());
  max_torque.setConstant(std::numeric_limits<double>::infinity());
}

bool JointLimits::IsValid() const {
  if (!IsSizeConsistent()) return false;

  if (size() == 0) {
    return true;
  }

  return (max_position - min_position).minCoeff() >= 0 &&
         (max_velocity.array() >= 0).all() &&
         (max_acceleration.array() >= 0).all() &&
         (max_jerk.array() >= 0).all() && (max_torque.array() >= 0).all();
}

using icon::RepeatedDoubleToVectorNd;
using icon::VectorNdToRepeatedDouble;

namespace {

bool IsInfiniteVector(const eigenmath::VectorNd& vec) {
  return std::any_of(vec.begin(), vec.end(),
                     [](double v) { return std::isinf(v); });
}

}  // namespace

intrinsic_proto::JointLimits ToProto(const JointLimits& limits) {
  intrinsic_proto::JointLimits limits_proto;
  VectorNdToRepeatedDouble(
      limits.min_position,
      limits_proto.mutable_min_position()->mutable_values());
  VectorNdToRepeatedDouble(
      limits.max_position,
      limits_proto.mutable_max_position()->mutable_values());
  if (!IsInfiniteVector(limits.max_velocity)) {
    VectorNdToRepeatedDouble(
        limits.max_velocity,
        limits_proto.mutable_max_velocity()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_acceleration)) {
    VectorNdToRepeatedDouble(
        limits.max_acceleration,
        limits_proto.mutable_max_acceleration()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_jerk)) {
    VectorNdToRepeatedDouble(limits.max_jerk,
                             limits_proto.mutable_max_jerk()->mutable_values());
  }
  if (!IsInfiniteVector(limits.max_torque)) {
    VectorNdToRepeatedDouble(
        limits.max_torque, limits_proto.mutable_max_effort()->mutable_values());
  }
  return limits_proto;
}

absl::StatusOr<JointLimits> FromProto(
    const intrinsic_proto::JointLimits& limits_proto) {
  INTRINSIC_ASSIGN_OR_RETURN(
      const eigenmath::VectorNd min_position,
      RepeatedDoubleToVectorNd(limits_proto.min_position().values()));

  INTRINSIC_RT_ASSIGN_OR_RETURN(JointLimits limits,
                                JointLimits::Unlimited(min_position.size()));

  limits.min_position = min_position;
  INTRINSIC_ASSIGN_OR_RETURN(
      limits.max_position,
      RepeatedDoubleToVectorNd(limits_proto.max_position().values()));
  if (limits_proto.has_max_velocity()) {
    INTRINSIC_ASSIGN_OR_RETURN(
        limits.max_velocity,
        RepeatedDoubleToVectorNd(limits_proto.max_velocity().values()));
  }
  if (limits_proto.has_max_acceleration()) {
    INTRINSIC_ASSIGN_OR_RETURN(
        limits.max_acceleration,
        RepeatedDoubleToVectorNd(limits_proto.max_acceleration().values()));
  }
  if (limits_proto.has_max_jerk()) {
    INTRINSIC_ASSIGN_OR_RETURN(
        limits.max_jerk,
        RepeatedDoubleToVectorNd(limits_proto.max_jerk().values()));
  }
  if (limits_proto.has_max_effort()) {
    INTRINSIC_ASSIGN_OR_RETURN(
        limits.max_torque,
        RepeatedDoubleToVectorNd(limits_proto.max_effort().values()));
  }
  if (!limits.IsValid()) {
    return absl::InvalidArgumentError(
        absl::StrCat("Joint limits proto are invalid:\n", limits_proto));
  }
  return limits;
}

JointLimits CreateSimpleJointLimits(int ndof, double max_position,
                                    double max_velocity,
                                    double max_acceleration, double max_jerk) {
  JointLimits limits;
  CHECK_OK(limits.SetSize(ndof));
  limits.SetUnlimited();
  for (int i = 0; i < ndof; ++i) {
    limits.min_position[i] = -max_position;
    limits.max_position[i] = max_position;
    limits.max_velocity[i] = max_velocity;
    limits.max_acceleration[i] = max_acceleration;
    limits.max_jerk[i] = max_jerk;
  }
  return limits;
}

JointLimits CreateSimpleJointLimits(int ndof, double max_position,
                                    double max_velocity,
                                    double max_acceleration, double max_jerk,
                                    double max_effort) {
  JointLimits limits;
  CHECK_OK(limits.SetSize(ndof));
  limits.SetUnlimited();
  for (int i = 0; i < ndof; ++i) {
    limits.min_position[i] = -max_position;
    limits.max_position[i] = max_position;
    limits.max_velocity[i] = max_velocity;
    limits.max_acceleration[i] = max_acceleration;
    limits.max_jerk[i] = max_jerk;
    limits.max_torque[i] = max_effort;
  }
  return limits;
}

absl::StatusOr<JointLimits> UpdateJointLimits(
    const JointLimits& base, const intrinsic_proto::JointLimitsUpdate& update) {
  JointLimits out = base;
  if (!update.min_position().values().empty()) {
    if (update.min_position().values_size() != base.min_position.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. min_position sizes are different. Base "
          "size: $0 Actual size: $1",
          base.min_position.size(), update.min_position().values_size()));
    }
    INTRINSIC_ASSIGN_OR_RETURN(
        out.min_position,
        RepeatedDoubleToVectorNd(update.min_position().values()));
  }
  if (!update.max_position().values().empty()) {
    if (update.max_position().values_size() != base.max_position.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_position sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_position.size(), update.max_position().values_size()));
    }
    INTRINSIC_ASSIGN_OR_RETURN(
        out.max_position,
        RepeatedDoubleToVectorNd(update.max_position().values()));
  }
  if (!update.max_velocity().values().empty()) {
    if (update.max_velocity().values_size() != base.max_velocity.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_velocity sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_velocity.size(), update.max_velocity().values_size()));
    }
    INTRINSIC_ASSIGN_OR_RETURN(
        out.max_velocity,
        RepeatedDoubleToVectorNd(update.max_velocity().values()));
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
    INTRINSIC_ASSIGN_OR_RETURN(
        out.max_acceleration,
        RepeatedDoubleToVectorNd(update.max_acceleration().values()));
  }
  if (!update.max_jerk().values().empty()) {
    if (update.max_jerk().values_size() != base.max_jerk.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_jerk sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_jerk.size(), update.max_jerk().values_size()));
    }
    INTRINSIC_ASSIGN_OR_RETURN(
        out.max_jerk, RepeatedDoubleToVectorNd(update.max_jerk().values()));
  }
  if (!update.max_effort().values().empty()) {
    if (update.max_effort().values_size() != base.max_torque.size()) {
      return absl::InvalidArgumentError(absl::Substitute(
          "Cannot update joint limits. max_effort sizes are different. Base "
          "size: $0 Actual size: $1",
          base.max_torque.size(), update.max_effort().values_size()));
    }
    INTRINSIC_ASSIGN_OR_RETURN(
        out.max_torque, RepeatedDoubleToVectorNd(update.max_effort().values()));
  }
  return out;
}

}  // namespace intrinsic
