// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include <iostream>
#include <memory>
#include <ostream>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080", "Address of the ICON Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_FLAG(std::string, header, "x-icon-instance-name",
          "Optional header name to be used to select a specific ICON instance. "
          " Has no effect if --instance is not set");

const char* UsageString() {
  return R"(
Usage: restart_server [--server=<addr>] [--instance=<name>]

Attempts to restart the entire ICON server.
The server waits until all sessions are ended, stops all hardware devices and
shuts down, then it starts again after a delay.
The ICON server receives the same signal as when the application is restarted.

This tool is not meant for typical operation, but only to apply exceptional
config changes in developer experiments (i.e. restarting ICON after adding
a plugin).

)";
}

namespace {

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params) {
  INTRINSIC_ASSIGN_OR_RETURN(auto icon_channel,
                             intrinsic::icon::Channel::Make(connection_params));
  return intrinsic::icon::Client(icon_channel).RestartServer();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(UsageString(), argc, argv);
  QCHECK_OK(Run(intrinsic::icon::ConnectionParams{
      .address = absl::GetFlag(FLAGS_server),
      .instance_name = absl::GetFlag(FLAGS_instance),
      .header = absl::GetFlag(FLAGS_header),
  }));
  std::cout << "Requested ICON server restart." << std::endl;
  return 0;
}
