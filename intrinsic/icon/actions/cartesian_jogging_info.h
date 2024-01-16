// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_ACTIONS_CARTESIAN_JOGGING_INFO_H_
#define INTRINSIC_ICON_ACTIONS_CARTESIAN_JOGGING_INFO_H_

#include "intrinsic/icon/actions/cartesian_jogging.pb.h"

namespace intrinsic {
namespace icon {

struct CartesianJoggingInfo {
  static constexpr char kActionTypeName[] = "xfa.cartesian_jogging";
  static constexpr char kActionDescription[] =
      "Generates and executes a Cartesian move with the given twist, using the "
      "default tracking and tool frames. The action starts with a zero twist "
      "at the current Cartesian pose and executes the twist commanded by "
      "non-realtime streaming commands. Movement is stopped if no streaming "
      "command is received within `kWatchdogTimeoutInSeconds` of the most "
      "recent streaming command. You are required to set appropriate cartesian "
      "velocity limits using `FixedParams`.";
  static constexpr char kSlotName[] = "arm";
  static constexpr char kSlotDescription[] =
      "The action moves this Part's end effector.";

  static constexpr char kStreamingInputName[] = "cartesian_jogging_command";
  static constexpr char kStreamingInputDescription[] =
      "Streaming twist with optional IK parameters. The robot accelerates "
      "and decelerates according to the limits set in 'FixedParams'.\n  "
      "Movement is stopped if no streaming command is received within "
      "'kWatchdogTimeoutInSeconds' of the most recent streaming command.";

  static constexpr char kTimedOut[] = "xfa.timed_out";
  static constexpr char kTimedOutDescription[] =
      "`Unavailable` before the action receives a streaming command. Switches "
      "to `False` when a streaming command is received.\n"
      "`True` after the watchdog (commanding a Zero Twist) is triggered.";

  // Time in seconds without new streaming command after which the watchdog
  // commands a Zero Twist.
  static constexpr double kWatchdogTimeoutInSeconds = 0.25;

  using FixedParams = ::xfa::icon::actions::proto::CartesianJoggingFixedParams;
  using StreamingParams =
      ::xfa::icon::actions::proto::CartesianJoggingStreamingParams;
};

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_ACTIONS_CARTESIAN_JOGGING_INFO_H_
