// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_ACTIONS_BLENDED_MOVE_ACTION_INFO_H_
#define INTRINSIC_ICON_ACTIONS_BLENDED_MOVE_ACTION_INFO_H_

#include "intrinsic/icon/actions/blended_move_action.pb.h"

namespace intrinsic::icon {

struct BlendedMoveActionInfo {
  static constexpr double kMaxInitialJointPositionDeviation =
      0.1;  // [rad], if the initial robot position deviates more from the
            // first trajectory position than this threshold, the Action will
            // return kFailedPrecondition.
  static constexpr double kMaxInitialJointVelocityDeviation =
      0.1;  // [rad/sec], if the initial robot velocity deviates more from the
            // first trajectory velocity than this threshold, the Action will
            // return kFailedPrecondition.

  static constexpr char kActionTypeName[] = "xfa.blended_move";
  static constexpr char kActionDescription[] =
      "Performs a time-optimal blended move through waypoints subject to given "
      "joint and Cartesian limits. Choose between blended joint "
      "space motion (linear joint space segments connected with parabolic "
      "blends) and blended linear Cartesian motion (linear Cartesian motion "
      "connected with parabolic blends). Both motion types will terminate with "
      "zero joint velocity. Online trajectory execution will slow down/speed "
      "up according to the speed override factor in a differentially "
      "consistent and time-optimal way. That is, accelerations will "
      "temporarily exceed the nominal trajectory accelerations (but not the "
      "system limits). This action also holds a settling state estimator which "
      "monitors residual oscillations or tracking error transients after the "
      "trajectory has been played back. See state variable documentation of "
      "`is_settled` for details.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] = "An arm part.";

  static constexpr char kTrajectoryProgress[] = "trajectory_progress";
  static constexpr char kTrajectoryProgressDescription[] =
      "A value between 0.0 and 1.0 describing the progress along the "
      "planned trajectory, where 1.0 means that the final setpoint has been "
      "reached. Describes the progress along setpoints, and not the actual "
      "physical robot state, which may deviate due to tracking error.";
  static constexpr char kIsSettled[] = "is_settled";
  static constexpr char kIsSettledDescription[] =
      "This Action reports 'is_settled==true' as soon as the robot has reached "
      "a settled state after executing the motion, and tracking errors and "
      "transients have decayed.";
  static constexpr char kBlendedMoveDoneForSeconds[] =
      "blended_move_done_for_seconds";
  static constexpr char kBlendedMoveDoneForSecondsDescription[] =
      "Time (in seconds) since the final setpoint was commanded. Will be zero "
      "in the cycle that the final setpoint is commanded and in all cycles "
      "before that.";

  using FixedParams = xfa::icon::actions::BlendedMoveActionFixedParams;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_ACTIONS_BLENDED_MOVE_ACTION_INFO_H_
