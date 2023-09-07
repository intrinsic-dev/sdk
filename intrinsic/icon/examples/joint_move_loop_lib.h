// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LOOP_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LOOP_LIB_H_

#include <memory>
#include <optional>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/examples/joint_move_positions.pb.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// Moves in a loop between two joint positions for the part `part_name` for
// `duration`. The first position is slightly off the center of the joint range
// and the second position is at the center of the joint range.
// The loop can optionally be parametrized via the `joint_move_positions`
// argument, specifying the two joint positions.

// A valid connection to an ICON server is passed in using the parameter
// `icon_channel`.
absl::Status RunJointMoveLoop(
    absl::string_view part_name, absl::Duration duration,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel,
    std::optional<intrinsic_proto::icon::JointMovePositions>
        joint_move_positions = std::nullopt);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LOOP_LIB_H_
