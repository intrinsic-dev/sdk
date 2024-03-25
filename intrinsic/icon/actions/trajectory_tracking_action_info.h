// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_ACTIONS_TRAJECTORY_TRACKING_ACTION_INFO_H_
#define INTRINSIC_ICON_ACTIONS_TRAJECTORY_TRACKING_ACTION_INFO_H_

#include "intrinsic/icon/actions/trajectory_tracking_action.pb.h"

namespace intrinsic::icon {

struct TrajectoryTrackingActionInfo {
  static constexpr double kMaxInitialJointPositionDeviation =
      0.1;  // [rad], if the initial robot position deviates more from the
            // first trajectory position than this threshold, the Action will
            // return kFailedPrecondition.
  static constexpr double kMaxInitialJointVelocityDeviation =
      0.15;  // [rad/sec], if the initial robot position deviates more from the
             // first trajectory position than this threshold, the Action will
             // return kFailedPrecondition.

  static constexpr char kActionTypeName[] = "xfa.trajectory_tracking";
  static constexpr char kActionDescription[] =
      "Tracks a given JointTrajectoryPVA provided as action parameter. The "
      "trajectory to be tracked is given as triples of joint positions, "
      "velocities and accelerations with time-stamps. This action assumes that "
      "the provided trajectory is feasible and performs no collision checking "
      "before or during execution. Employs a differentially consistent spline "
      "for fine-interpolation between provided setpoints. Trajectory execution "
      "will slow down/speed up according to the speed override factor in a "
      "differentially consistent and time-optimal way. That is, accelerations "
      "will temporarily exceed the nominal trajectory accelerations (but not "
      "the system limits). The provided trajectory must not violate the system "
      "limits. This action also holds a settling state estimator which "
      "monitors residual oscillations or tracking error transients after the "
      "trajectory has been played back, see state variable documentation for "
      "`is_settled`. If the provided trajectory ends in a non-zero velocity "
      "terminal state, the caller is responsible for appending a "
      "differentially consistent motion or controller, too.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] = "An arm part.";

  static constexpr char kIsSettled[] = "is_settled";
  static constexpr char kIsSettledDescription[] =
      "This Action reports 'settled' as soon as the robot has reached a "
      "settled state after tracking the prescribed motion trajectory, only if "
      "its target velocity was zero.";
  static constexpr char kIsSettledUncertainty[] = "is_settled_uncertainty";
  static constexpr char kIsSettledUncertaintyDescription[] =
      "Reports the uncertainty in the belief if the robot has settled or not "
      "as a continuous measure in the range [0,1]. 1 means maximum uncertainty "
      "(robot is not settled), and 0 minimum uncertainty (robot has settled). ";
  static constexpr char kTrajectoryProgress[] = "trajectory_progress";
  static constexpr char kTrajectoryProgressDescription[] =
      "A value between 0.0 and 1.0 describing the progress along the "
      "nominal trajectory, where 1.0 means that the final setpoint has been "
      "reached. Describes the progress along setpoints, and not the actual "
      "physical robot state.";
  static constexpr char kDistanceToFinalSetpoint[] =
      "distance_to_final_setpoint";
  static constexpr char kDistanceToFinalSetpointDescription[] =
      "Euclidean norm of the difference between the final trajectory position "
      "setpoint and the currently sensed joint position.";
  static constexpr char kTrajectoryDoneForSeconds[] =
      "trajectory_done_for_seconds";
  static constexpr char kTrajectoryDoneForSecondsDescription[] =
      "Time (in seconds) since the final setpoint was commanded. Will be zero "
      "in the cycle that the final setpoint is commanded and in all cycles "
      "before that.";

  static constexpr char kSignalPathAccurateStop[] = "signal_path_accurate_stop";
  static constexpr char kSignalPathAccurateStopDescription[] =
      "Requests a path-accurate stop along the given trajectory. The "
      "path-accurate stop is guaranteed to be time-optimal w.r.t. the given "
      "system limits.";

  using FixedParams = xfa::icon::actions::TrajectoryTrackingActionFixedParams;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_ACTIONS_TRAJECTORY_TRACKING_ACTION_INFO_H_
