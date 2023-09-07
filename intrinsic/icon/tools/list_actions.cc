// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include <algorithm>
#include <iostream>
#include <iterator>
#include <ostream>
#include <string>
#include <vector>

#include "absl/flags/flag.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/tools/generate_documentation.h"
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
ABSL_FLAG(bool, show_details, false,
          "Outputs action signature details in markdown format.");

const char* UsageString() {
  return R"(
Usage: list_actions [--server=<addr>] [--instance=<name>] [--show_details]

Lists available actions from an ICON Application Layer Service.

By default, the output only shows action type names:

    list_actions

```
xfa.point_to_point_move
xfa.cartesian_position
```

Add `--show_details` to also show details in markdown format which include the
action's description text, compatible parts, fixed parameters, streaming inputs,
streaming outputs, and state variables.

    list_actions --show_details

```
# xfa.joint_position_move
Move part to goal position in joint space.

## Compatible Parts
- tigerstar_left_arm
- tigerstar_right_arm

## Fixed Parameters

### controller
Joint controller selection and controller-specific parameters.

### done_distance_to_goal
Distance in meters to goal below which the `done` state variable becomes
True.

### goal_position
Target joint position.

### limits
Motion-specific limits. Actual limits used will be the most conservative of
(i) HAL-configured limits, (ii) session-configured limits and (iii) these
motion-specific limits.

## Streaming Inputs
(none)

## Streaming Outputs
(none)

## State Variables
(none)
```

)";
}

namespace intrinsic {
namespace icon {
namespace {

absl::StatusOr<std::string> Run(
    const intrinsic::icon::ConnectionParams& connection_params,
    bool show_details) {
  // Fetch action signatures.
  INTRINSIC_ASSIGN_OR_RETURN(auto icon_channel,
                             Channel::Make(connection_params));
  Client icon_client(icon_channel);
  INTRINSIC_ASSIGN_OR_RETURN(
      std::vector<intrinsic_proto::icon::ActionSignature> signatures,
      icon_client.ListActionSignatures());
  if (signatures.empty()) {
    return "(No actions available)\n";
  }

  if (!show_details) {
    return GenerateActionNames(signatures);
  }

  std::vector<std::vector<std::string>> actions_compatible_parts;
  for (const intrinsic_proto::icon::ActionSignature& signature : signatures) {
    std::vector<std::string> compatible_parts;
    if (auto status_or_parts =
            icon_client.ListCompatibleParts({signature.action_type_name()});
        status_or_parts.ok()) {
      compatible_parts = *status_or_parts;
    } else {
      compatible_parts = {
          absl::StrCat("(Error fetching list of compatible parts: ",
                       status_or_parts.status().ToString(), ")")};
    }
    actions_compatible_parts.emplace_back(compatible_parts);
  }
  return GenerateDocumentation(signatures, actions_compatible_parts);
}

}  // namespace
}  // namespace icon
}  // namespace intrinsic

int main(int argc, char** argv) {
  InitXfa(UsageString(), argc, argv);

  absl::StatusOr<std::string> result = intrinsic::icon::Run(
      intrinsic::icon::ConnectionParams{
          .address = absl::GetFlag(FLAGS_server),
          .instance_name = absl::GetFlag(FLAGS_instance),
          .header = absl::GetFlag(FLAGS_header),
      },
      absl::GetFlag(FLAGS_show_details));
  if (!result.ok()) {
    LOG(ERROR) << result.status() << std::endl;
    return 1;
  }

  std::cout << *result;

  return 0;
}
