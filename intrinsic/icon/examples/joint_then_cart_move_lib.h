// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_

#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// 1. Performs a joint move to a constand, valid joint position.
// 2. Waits until position is settled.
// 3. Performs a small Cartesian move (Cartesian jogging) in +X direction.
//
// The parameter `part_name` defines the part that is controlled using
// `icon_channel`.
absl::Status JointThenCartMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_JOINT_THEN_CART_MOVE_LIB_H_
