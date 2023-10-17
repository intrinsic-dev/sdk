// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/actions/point_to_point_move_info.h"

#include "absl/types/span.h"
#include "intrinsic/icon/proto/joint_space.pb.h"
#include "intrinsic/kinematics/types/joint_limits.h"

namespace intrinsic {
namespace icon {

PointToPointMoveInfo::FixedParams CreatePointToPointMoveFixedParams(
    absl::Span<const double> goal_position,
    absl::Span<const double> goal_velocity) {
  PointToPointMoveInfo::FixedParams fixed_params;
  *fixed_params.mutable_goal_position()->mutable_joints() = {
      goal_position.begin(), goal_position.end()};
  *fixed_params.mutable_goal_velocity()->mutable_joints() = {
      goal_velocity.begin(), goal_velocity.end()};
  return fixed_params;
}

PointToPointMoveInfo::FixedParams CreatePointToPointMoveFixedParams(
    absl::Span<const double> goal_position,
    absl::Span<const double> goal_velocity, const JointLimits& joint_limits) {
  PointToPointMoveInfo::FixedParams fixed_params;
  *fixed_params.mutable_goal_position()->mutable_joints() = {
      goal_position.begin(), goal_position.end()};
  *fixed_params.mutable_goal_velocity()->mutable_joints() = {
      goal_velocity.begin(), goal_velocity.end()};
  *fixed_params.mutable_joint_limits() = ToProto(joint_limits);
  return fixed_params;
}

}  // namespace icon
}  // namespace intrinsic
