// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LIB_H_

#include <memory>

#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// First moves all joints to a position offset from the joint range center, then
// switches to the stop action and then moves the joints to the center of the
// joint range.
// Controls the part defined by `part_name` using the provided `icon_channel`.
absl::Status RunJointMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);
}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_JOINT_MOVE_LIB_H_
