// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_EXAMPLES_SIMPLE_GRIPPER_LIB_H_
#define INTRINSIC_ICON_EXAMPLES_SIMPLE_GRIPPER_LIB_H_

#include <cstddef>
#include <memory>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/actions/simple_gripper_info.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/util/grpc/channel_interface.h"

namespace intrinsic::icon::examples {

// Requests the status for `part_name` and prints it to std::cout.
// Returns NotFoundError if no status for that part is returned.
absl::Status PrintPartStatus(absl::string_view part_name, Client& icon_client);

// Opens a session for `part_name`, sends the command defined by
// `action_parameters` and waits for the condition
// SimpleGripperActionInfo::kSentCommand.
absl::Status SendGripperCommand(
    absl::string_view part_name,
    const SimpleGripperActionInfo::FixedParams& action_parameters,
    std::shared_ptr<ChannelInterface> icon_channel);

// Sends a GRASP command to `part_name`, prints the part status to std::cout,
// then waits 10s, sends a RELEASE command and prints the part status to
// std::cout.
absl::Status ExampleGraspAndRelease(
    absl::string_view part_name,
    std::shared_ptr<ChannelInterface> icon_channel);

}  // namespace intrinsic::icon::examples

#endif  // INTRINSIC_ICON_EXAMPLES_SIMPLE_GRIPPER_LIB_H_
