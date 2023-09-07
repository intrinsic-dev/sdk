// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/cc_client/robot_config.h"

#include <string>
#include <string_view>
#include <vector>

#include "absl/algorithm/container.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {
namespace icon {

absl::StatusOr<intrinsic_proto::icon::PartConfig> RobotConfig::FindPartConfig(
    absl::string_view part_name) const {
  // Lookup part config in repeated field by part name.
  auto part_config = absl::c_find_if(
      config_proto_.part_configs(),
      [&](const intrinsic_proto::icon::PartConfig& part_config) {
        return part_config.name() == part_name;
      });
  if (part_config == config_proto_.part_configs().end()) {
    return absl::NotFoundError(absl::StrCat(
        "Part named \"", part_name, "\" not found in robot part config."));
  }
  return *part_config;
}

absl::StatusOr<intrinsic_proto::icon::GenericPartConfig>
RobotConfig::GetGenericPartConfig(absl::string_view part_name) const {
  INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartConfig part_config,
                             FindPartConfig(part_name));
  return part_config.generic_config();
}

absl::StatusOr<google::protobuf::Any> RobotConfig::GetPartConfigAny(
    absl::string_view part_name) const {
  INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartConfig part_config,
                             FindPartConfig(part_name));
  return part_config.config();
}

absl::StatusOr<std::vector<intrinsic_proto::icon::FeatureInterfaceTypes>>
RobotConfig::GetPartFeatureInterfaces(absl::string_view part_name) const {
  INTRINSIC_ASSIGN_OR_RETURN(intrinsic_proto::icon::PartConfig part_config,
                             FindPartConfig(part_name));
  std::vector<intrinsic_proto::icon::FeatureInterfaceTypes> out;
  out.reserve(part_config.feature_interfaces().size());
  for (int fi : part_config.feature_interfaces()) {
    out.emplace_back(
        static_cast<intrinsic_proto::icon::FeatureInterfaceTypes>(fi));
  }
  return out;
}

double RobotConfig::GetControlFrequency() const {
  return config_proto_.control_frequency_hz();
}

std::string_view RobotConfig::GetServerName() const {
  return config_proto_.server_config().name();
}

}  // namespace icon
}  // namespace intrinsic
