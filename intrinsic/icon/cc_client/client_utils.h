// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CC_CLIENT_CLIENT_UTILS_H_
#define INTRINSIC_ICON_CC_CLIENT_CLIENT_UTILS_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/cc_client/robot_config.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {
namespace icon {

// Obtains the part-specific configuration info for `part_name` unpacked into
// a `ConfigT`. `ConfigT` must match the part's `config_message_type` in its
// `proto::PartSignature`.
//
// If getting the config for multiple parts, then Client::GetConfig() is
// preferred because it is more efficient (it avoids multiple round-trips to the
// server).
template <typename ConfigT>
absl::StatusOr<ConfigT> GetPartConfig(const Client& client,
                                      absl::string_view part_name) {
  INTRINSIC_ASSIGN_OR_RETURN(RobotConfig robot_config, client.GetConfig());
  return robot_config.GetPartConfig<ConfigT>(part_name);
}

// Describes a Condition that is satisfied when an action has finished.
//
// Equivalent to `IsTrueCondition(kIsDone)`.
Comparison IsDone();

// Convenience function for setting a single part property (with double value).
// If setting multiple properties, it is more efficient to call
// `client.SetPartProperties`.
absl::Status SetPartProperty(const Client& client, absl::string_view part_name,
                             absl::string_view property_name,
                             double double_value);

// Convenience function for setting a single part property (with bool value).
// If setting multiple properties, it is more efficient to call
// `client.SetPartProperties`.
absl::Status SetPartProperty(const Client& client, absl::string_view part_name,
                             absl::string_view property_name, bool bool_value);

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_CC_CLIENT_CLIENT_UTILS_H_
