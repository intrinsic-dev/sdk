// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_

#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// 1. Performs a Point to Point Move to a Starting Position,
// 2. Stops and stores the Cartesian Pose of the End Effector.
// 3. Performs a Point to Point Move away from the Starting Position.
// 4. Performs a Cartesian Motion back to the stored Cartesian Pose of the End
// Effector.
//
// The parameter `part_name` defines the part that is controlled using
// `icon_channel`.
absl::Status JointThenCartMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_
