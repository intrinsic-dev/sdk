// Copyright 2023 Intrinsic Innovation LLC

// The `show_joint_angles` tool displays the joint values for a part.
#include <cstddef>
#include <iostream>
#include <memory>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/operational_status.h"
#include "intrinsic/icon/proto/part_status.pb.h"
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

ABSL_FLAG(std::string, part, "arm", "Part to get joint angles for");

ABSL_FLAG(double, refresh, 0.75,
          "Seconds between refreshes; if 0: prints angles once");

const char* UsageString() {
  return R"(
Usage: show_joint_angles [--server=<addr>] [--instance=<name>] [--part=<part>] [--refresh=<seconds>]

Displays a part's joint angles.

Example:

  show_joint_angles

This will refresh every 0.75 seconds, by default. To refresh at a different rate (in seconds), use, for example:

  show_joint_angles --refresh=2.5

To print the joint values once and immediately exit, use:

  show_joint_angles --refresh=0
)";
}

namespace {

using intrinsic::icon::Channel;
using intrinsic::icon::Client;
using intrinsic::icon::OperationalStatus;
using intrinsic::icon::ToString;
using intrinsic_proto::icon::PartStatus;

absl::Status StrAppendJointAngles(std::string* out, const Client& client,
                                  absl::string_view part) {
  absl::StatusOr<PartStatus> part_status = client.GetSinglePartStatus(part);
  if (!part_status.ok()) {
    return part_status.status();
  }
  for (size_t i = 0; i < part_status->joint_states_size(); ++i) {
    const intrinsic_proto::icon::PartJointState& joint_state =
        part_status->joint_states(i);
    absl::StrAppend(out, "J", i + 1, ":",
                    absl::StrFormat("%6.3f", joint_state.position_sensed()),
                    "\n");
  }
  return absl::OkStatus();
}

absl::Status Run(const intrinsic::icon::ConnectionParams& connection_params,
                 absl::string_view part, double refresh) {
  INTRINSIC_ASSIGN_OR_RETURN(auto icon_channel,
                             Channel::Make(connection_params));
  Client client(icon_channel);
  if (refresh == 0) {
    // --refresh=0; run once and quit.
    std::string out;
    absl::Status status = StrAppendJointAngles(&out, client, part);
    std::cout << out;
    return absl::OkStatus();
  }
  while (true) {
    std::string out = "\033[2J";  // Clear the screen.
    absl::Time start = absl::Now();
    absl::StrAppend(
        &out,
        "Time: ", absl::FormatTime("%H:%M:%E3S", start, absl::LocalTimeZone()),
        "\n");
    if (absl::StatusOr<OperationalStatus> operational_status =
            client.GetOperationalStatus();
        operational_status.ok()) {
      absl::StrAppend(
          &out, "Operational Status: ", ToString(*operational_status), "\n");
    }
    if (absl::Status status = StrAppendJointAngles(&out, client, part);
        !status.ok()) {
      return status;
    }
    absl::StrAppend(&out, "Press ctrl-C to quit.\n");
    std::cout << out;
    absl::SleepFor(start + absl::Seconds(refresh) - absl::Now());
  }
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
      absl::GetFlag(FLAGS_part), absl::GetFlag(FLAGS_refresh)));
  return 0;
}
