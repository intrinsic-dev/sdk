// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

// The `list_parts` binary is a tool that lists available robot parts from an
// Icon Application Layer Service.
//
//
#include <iostream>
#include <ostream>
#include <string>
#include <vector>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
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

namespace {

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params) {
  INTRINSIC_ASSIGN_OR_RETURN(auto icon_channel,
                             intrinsic::icon::Channel::Make(connection_params));
  INTRINSIC_ASSIGN_OR_RETURN(auto parts,
                             intrinsic::icon::Client(icon_channel).ListParts());
  for (const auto& part_name : parts) {
    std::cout << part_name << std::endl;
  }

  return absl::OkStatus();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);

  QCHECK_OK(Run(intrinsic::icon::ConnectionParams{
      .address = absl::GetFlag(FLAGS_server),
      .instance_name = absl::GetFlag(FLAGS_instance),
      .header = absl::GetFlag(FLAGS_header),
  }));

  return 0;
}
