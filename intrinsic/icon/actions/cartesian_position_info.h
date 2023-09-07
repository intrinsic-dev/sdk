// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_ACTIONS_CARTESIAN_POSITION_INFO_H_
#define INTRINSIC_ICON_ACTIONS_CARTESIAN_POSITION_INFO_H_

#include "intrinsic/icon/actions/cartesian_position.pb.h"

namespace intrinsic {
namespace icon {

struct CartesianPositionInfo {
  static constexpr char kActionTypeName[] = "xfa.cartesian_position";
  static constexpr char kActionDescription[] =
      "Generates and executes a cartesian move to the given 6D pose, using the "
      "default tracking and tool frames. This action is only intended for "
      "small moves, because the underlying kinematics solvers do not "
      "simulatenously respect target poses and joint limits.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] =
      "The action moves this Part's end effector to the desired pose.";
  static constexpr char kIsDoneDescription[] =
      "This Action reports 'done' as soon as the last setpoint is commanded. "
      "This might not coincide with the robot actually reaching that setpoint.";
  static constexpr char kLinearDistanceToGoal[] =
      "xfa.distance_to_sensed_linear";
  static constexpr char kLinearDistanceToGoalDescription[] =
      "Absolute linear distance between the sensed pose and the goal pose.";
  static constexpr char kAngularDistanceToGoal[] =
      "xfa.distance_to_sensed_angular";
  static constexpr char kAngularDistanceToGoalDescription[] =
      "Absolute angular distance between the sensed joint pose and the goal "
      "pose.";

  using FixedParams = ::xfa::icon::actions::proto::CartesianPositionFixedParams;
};

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_ACTIONS_CARTESIAN_POSITION_INFO_H_
