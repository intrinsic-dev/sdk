// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_ACTIONS_WAIT_FOR_SETTLING_ACTION_INFO_H_
#define INTRINSIC_ICON_ACTIONS_WAIT_FOR_SETTLING_ACTION_INFO_H_

#include "intrinsic/icon/actions/wait_for_settling_action.pb.h"

namespace intrinsic::icon {

struct WaitForSettlingActionInfo {
  static constexpr char kActionTypeName[] = "xfa.wait_for_settling_action";
  static constexpr char kActionDescription[] =
      "Action that monitors joint velocity signals and waits until all "
      "long-lasting transients have vanished.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] =
      "The Action monitors the sensed joint velocities of this arm and sends "
      "zero joint velocities command until the sensed joint velocities settle "
      "to zero.";
  static constexpr char kIsDoneDescription[] =
      "This Action reports 'is_done==true' as soon as residual oscillations "
      "and/or tracking errors have decayed and the robot has reached a settled "
      "state.";
  static constexpr char kActionElapsedTimeSeconds[] = "elapsed_time_seconds";
  static constexpr char kActionElapsedTimeSecondsDescription[] =
      "Time elapsed running this action in [s].";
  static constexpr char kMaximumJointVelocityMagnitude[] =
      "maximum_joint_velocity_magnitude";
  static constexpr char kMaximumJointVelocityMagnitudeDescription[] =
      "The maximum joint velocity magnitude (across all joints) at the current "
      "time in [rad/s].";

  using FixedParams =
      ::xfa::icon::actions::proto::WaitForSettlingActionFixedParams;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_ACTIONS_WAIT_FOR_SETTLING_ACTION_INFO_H_
