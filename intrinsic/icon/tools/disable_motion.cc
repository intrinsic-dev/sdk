// Copyright 2023 Intrinsic Innovation LLC

// The `disable_motion` tool attempts to put the ICON Server into the DISABLED
// operational state.
#include <iostream>
#include <memory>
#include <ostream>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080", "Address of the ICON Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_FLAG(std::string, header, "x-icon-instance-name",
          "Optional header name to be used to select a specific ICON instance. "
          " Has no effect if --instance is not set");
ABSL_FLAG(bool, clear_faults, false, "Clear faults when disabling");

const char* UsageString() {
  return R"(
Usage: disable_motion [--server=<addr>] [--instance=<name>] [--clear_faults]

Attempts to put the ICON Server into the DISABLED operational state.

Example:

    disable_motion

If the ICON Server is already DISABLED, this is a no-op.

If the ICON Server is the in the FAULTED operational state, you can use
--clear_faults to clear the fault, leaving the server in the DISABLED state.

    disable_motion --clear_faults
)";
}

namespace {

using intrinsic::icon::Channel;
using intrinsic::icon::Client;
using intrinsic::icon::IsFaulted;
using intrinsic::icon::OperationalStatus;

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params,
                 bool clear_faults) {
  INTR_ASSIGN_OR_RETURN(auto icon_channel, Channel::Make(connection_params));
  Client client(icon_channel);
  if (clear_faults) {
    if (absl::Status status = client.ClearFaults(); !status.ok()) {
      return absl::Status(
          status.code(),
          absl::StrCat("Unable to clear faults: ", status.message()));
    }
    std::cout << "Faults cleared." << std::endl;
  } else if (absl::StatusOr<OperationalStatus> operational_status =
                 client.GetOperationalStatus();
             operational_status.ok() && IsFaulted(*operational_status)) {
    return absl::FailedPreconditionError(absl::StrCat(
        "ICON Server is ", ToString(*operational_status),
        ". Use `disable_motion --server=", connection_params.address,
        " --clear_faults` to clear faults."));
  }
  return client.Disable();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(UsageString(), argc, argv);
  QCHECK_OK(Run(
      intrinsic::icon::ConnectionParams{
          .address = absl::GetFlag(FLAGS_server),
          .instance_name = absl::GetFlag(FLAGS_instance),
          .header = absl::GetFlag(FLAGS_header),
      },
      absl::GetFlag(FLAGS_clear_faults)));
  std::cout << "Disabled." << std::endl;
  return 0;
}
