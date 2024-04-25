// Copyright 2023 Intrinsic Innovation LLC

#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/examples/joint_move_lib.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080",
          "Address of the ICON Application Layer Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_RETIRED_FLAG(std::string, header, "x-icon-instance-name", "retired");
ABSL_FLAG(std::string, part, "arm", "Part to control.");

const char kUsage[] =
    "Moves all joints to a position slightly offset from the center of the "
    "joint range, switches to the stop action and performs a joint move "
    "towards the center of the joint range.";

namespace {

absl::Status Run(const intrinsic::ConnectionParams& connection_params,
                 absl::string_view part_name) {
  if (connection_params.address.empty()) {
    return absl::FailedPreconditionError("`--server` must not be empty.");
  }
  if (part_name.empty()) {
    return absl::FailedPreconditionError("`--part` must not be empty.");
  }

  INTR_ASSIGN_OR_RETURN(auto icon_channel,
                        intrinsic::icon::Channel::Make(connection_params));

  return intrinsic::icon::examples::RunJointMove(part_name, icon_channel);
}
}  // namespace

int main(int argc, char** argv) {
  InitXfa(kUsage, argc, argv);
  QCHECK_OK(Run(intrinsic::ConnectionParams::ResourceInstance(
                    absl::GetFlag(FLAGS_instance), absl::GetFlag(FLAGS_server)),
                absl::GetFlag(FLAGS_part)));
  return 0;
}
