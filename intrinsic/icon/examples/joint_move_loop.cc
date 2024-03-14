// Copyright 2023 Intrinsic Innovation LLC

#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/time/time.h"
#include "intrinsic/icon/examples/joint_move_loop_lib.h"
#include "intrinsic/icon/examples/joint_move_positions.pb.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/proto/get_text_proto.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080",
          "Address of the ICON Application Layer Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_FLAG(std::string, header, "x-resource-instance-name",
          "Optional header name to be used to select a specific ICON instance. "
          " Has no effect if --instance is not set");
ABSL_FLAG(std::string, part, "arm", "Part to control.");

ABSL_FLAG(absl::Duration, duration, absl::Minutes(1),
          "Defines how long the robot should loop through the joint moves. "
          "Examples: 30s, 1m");
ABSL_FLAG(std::string, joint_move_position_config, "",
          "Optional joint move positions to use in this loop.");

const char kUsage[] =
    "Moves in a loop between two joints positions. The first position is "
    "slightly off the center of the joint range and the second position is at "
    "the center of the joint range.";

namespace {

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params,
                 std::string_view part_name, absl::Duration duration,
                 std::string_view joint_move_position_config) {
  if (connection_params.address.empty()) {
    return absl::FailedPreconditionError("`--server` must not be empty.");
  }
  if (part_name.empty()) {
    return absl::FailedPreconditionError("`--part` must not be empty.");
  }

  INTR_ASSIGN_OR_RETURN(auto icon_channel,
                        intrinsic::icon::Channel::Make(connection_params));

  std::optional<intrinsic_proto::icon::JointMovePositions>
      joint_move_positions = std::nullopt;
  if (!joint_move_position_config.empty()) {
    intrinsic_proto::icon::JointMovePositions joint_pos;
    INTR_RETURN_IF_ERROR(
        intrinsic::GetTextProto(joint_move_position_config, joint_pos));
    joint_move_positions.emplace(std::move(joint_pos));
  }

  return intrinsic::icon::examples::RunJointMoveLoop(
      part_name, duration, icon_channel, std::move(joint_move_positions));
}
}  // namespace

int main(int argc, char** argv) {
  InitXfa(kUsage, argc, argv);
  QCHECK_OK(Run(
      intrinsic::icon::ConnectionParams{
          .address = absl::GetFlag(FLAGS_server),
          .instance_name = absl::GetFlag(FLAGS_instance),
          .header = absl::GetFlag(FLAGS_header),
      },
      absl::GetFlag(FLAGS_part), absl::GetFlag(FLAGS_duration),
      absl::GetFlag(FLAGS_joint_move_position_config)));
  return 0;
}
