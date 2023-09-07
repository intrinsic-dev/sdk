// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_ACTIONS_POINT_TO_POINT_MOVE_INFO_H_
#define INTRINSIC_ICON_ACTIONS_POINT_TO_POINT_MOVE_INFO_H_

#include "absl/types/optional.h"
#include "absl/types/span.h"
#include "intrinsic/icon/actions/point_to_point_move.pb.h"
#include "intrinsic/kinematics/types/joint_limits.h"

namespace intrinsic {
namespace icon {

// Contains information needed by clients to correctly describe a point-to-point
// move action.
struct PointToPointMoveInfo {
  // PointToPointMove action type name and description
  static constexpr char kActionTypeName[] = "xfa.point_to_point_move";
  static constexpr char kActionDescription[] =
      "Generates and executes a jerk-limited time-optimal trajectory to move "
      "the part's joints to the desired target position. Uses Reflexxes for "
      "instantaneous real-time motion generation. For motions with zero "
      "initial and target joint velocity, or co-linear initial and final "
      "velocity, the resulting trajectory will typically be linear in "
      "joint-space. Otherwise, there are no guarantees on the geometric shape "
      "of the joint move. Online trajectory execution will slow down/speed "
      "up according to the speed override factor in a differentially "
      "consistent and time-optimal way. This action also holds a settling "
      "state estimator which monitors residual oscillations or tracking error "
      "transients after the trajectory has been played back. See state "
      "variable documentation of `xfa.is_settled` for details.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] =
      "The action moves this Part in joint space.";
  static constexpr char kIsDoneDescription[] =
      "This Action reports 'done' as soon as the last setpoint is commanded. "
      "This might not coincide with the robot actually reaching that setpoint.";
  static constexpr char kIsSettled[] = "xfa.is_settled";
  static constexpr char kIsSettledDescription[] =
      "This Action reports 'settled' as soon as the robot has reached a "
      "settled state with zero joint velocity after executing the motion.";
  static constexpr char kDistanceToSensed[] = "xfa.distance_to_sensed";
  static constexpr char kDistanceToSensedDescription[] =
      "Euclidean norm of the difference between the final setpoint and the "
      "sensed joint position.";
  static constexpr char kSetpointDoneForSeconds[] =
      "xfa.setpoint_done_for_seconds";
  static constexpr char kSetpointDoneForSecondsDescription[] =
      "Time (in seconds) since the final setpoint was commanded. Can be zero "
      "in the cycle that the final setpoint is commanded. Only "
      "available as soon as the Action is done (i.e. has sent the final "
      "setpoint). Conditions that use this variable will always evaluate to "
      "false until then.";

  using FixedParams = ::xfa::icon::actions::proto::PointToPointMoveFixedParams;
};

// Returns a set of fixed params for this action that specifies the
// `goal_position` and `goal_velocity`. The size of the goal spans is determined
// by the number of joints on the part being controlled.
PointToPointMoveInfo::FixedParams CreatePointToPointMoveFixedParams(
    absl::Span<const double> goal_position,
    absl::Span<const double> goal_velocity);

// Returns a set of fixed params for this action that specifies the
// `goal_position` and `goal_velocity` and `joint_limits`. The size of the goal
// spans is determined by the number of joints on the part being controlled.
PointToPointMoveInfo::FixedParams CreatePointToPointMoveFixedParams(
    absl::Span<const double> goal_position,
    absl::Span<const double> goal_velocity, const JointLimits& joint_limits);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_ACTIONS_POINT_TO_POINT_MOVE_INFO_H_
