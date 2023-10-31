// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_EXAMPLES_BLENDED_CARTESIAN_MOVE_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_BLENDED_CARTESIAN_MOVE_LIB_H_

#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// Executes a blended Cartesian move for the part with `part_name`. A valid
// connection to an ICON server is passed in using the parameter `icon_channel`.
absl::Status RunBlendedCartesianMove(
    absl::string_view part_name,
    std::shared_ptr<intrinsic::icon::ChannelInterface> icon_channel);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_BLENDED_CARTESIAN_MOVE_LIB_H_
