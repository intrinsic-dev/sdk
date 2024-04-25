// Copyright 2023 Intrinsic Innovation LLC

// The `clear_faults` tool connects to an ICON Server and clears any faults.
// After this, ICON should automatically enable, and allow users to create
// Sessions.
#include <iostream>
#include <memory>
#include <ostream>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/operational_status.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/util/grpc/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, server, "xfa.lan:17080", "Address of the ICON Server");
ABSL_FLAG(
    std::string, instance, "",
    "Optional name of the ICON instance. Use this to select a specific ICON "
    "instance if multiple ones are running behind an ingress server.");
ABSL_RETIRED_FLAG(std::string, header, "x-icon-instance-name", "retired");
ABSL_FLAG(bool, print_fault_reason, false,
          "Prints the fault reason, if any, before clearing the fault.");

const char* UsageString() {
  return R"(
Usage: clear_faults [--server=<addr>] [--instance=<name>] [--header=<name>]

Connects to an ICON Server and clears any faults.
After this, ICON should automatically enable, and allow users to create
Sessions.

Example:

    clear_faults --instance=ur3e --header=x-resource-instance-name

If the ICON Server is not currently FAULTED, this is a no-op.

If you pass --print_fault_reason, the tool prints the reason for a pre-existing fault, if any.
)";
}

namespace {

absl::Status Run(const intrinsic::ConnectionParams& connection_params,
                 bool print_fault_reason) {
  INTR_ASSIGN_OR_RETURN(auto icon_channel,
                        intrinsic::icon::Channel::Make(connection_params));
  intrinsic::icon::Client client(icon_channel);
  INTR_ASSIGN_OR_RETURN(intrinsic::icon::OperationalStatus status,
                        client.GetOperationalStatus());
  if (!intrinsic::icon::IsFaulted(status)) {
    LOG(INFO) << "ICON is not faulted.";
    return absl::OkStatus();
  }
  if (print_fault_reason) {
    LOG(INFO) << "Fault reason: " << status.fault_reason();
  }
  if (absl::Status status = client.ClearFaults(); !status.ok()) {
    return absl::Status(status.code(), absl::StrCat("Unable to clear faults: ",
                                                    status.message()));
  }
  return absl::OkStatus();
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(UsageString(), argc, argv);
  QCHECK_OK(Run(intrinsic::ConnectionParams::ResourceInstance(
                    absl::GetFlag(FLAGS_instance), absl::GetFlag(FLAGS_server)),
                absl::GetFlag(FLAGS_print_fault_reason)));
  std::cout << "Cleared Faults." << std::endl;
  return 0;
}
