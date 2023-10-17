// Copyright 2023 Intrinsic Innovation LLC

#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/examples/adio_lib.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080",
          "Address of the ICON Application Layer Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_FLAG(std::string, header, "x-icon-instance-name",
          "Optional header name to be used to select a specific ICON instance. "
          " Has no effect if --instance is not set");
ABSL_FLAG(std::string, part, "adio", "Part to control.");

ABSL_FLAG(std::string, output_block, "outputs",
          "Name of the output_block to set bits.");

const char kUsage[] =
    "Sets the two lowest bits of 'output_block' to '1', then waits 10s and "
    "clears them again.";

namespace {

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params,
                 absl::string_view part_name,
                 absl::string_view output_block_name) {
  if (connection_params.address.empty()) {
    return absl::FailedPreconditionError("`--server` must not be empty.");
  }
  if (part_name.empty()) {
    return absl::FailedPreconditionError("`--part` must not be empty.");
  }

  INTRINSIC_ASSIGN_OR_RETURN(auto icon_channel,
                             intrinsic::icon::Channel::Make(connection_params));

  return intrinsic::icon::examples::ExampleSetDigitalOutput(
      part_name, output_block_name, icon_channel);
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
      absl::GetFlag(FLAGS_part), absl::GetFlag(FLAGS_output_block)));
  return 0;
}
