// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CC_CLIENT_ROBOT_CONFIG_H_
#define INTRINSIC_ICON_CC_CLIENT_ROBOT_CONFIG_H_

#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/icon/proto/generic_part_config.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic {
namespace icon {

// Snapshot of the robot config, including part-specific config.
class RobotConfig {
 public:
  // Constructs a RobotConfig from a `proto::GetConfigResponse`.
  explicit RobotConfig(intrinsic_proto::icon::GetConfigResponse config_proto)
      : config_proto_(std::move(config_proto)) {}

  // Obtains the generic config for `part_name` from this RobotConfig. The
  // generic config has most information about a part, without requiring the
  // user to correctly identify a part-specific type.
  absl::StatusOr<intrinsic_proto::icon::GenericPartConfig> GetGenericPartConfig(
      absl::string_view part_name) const;

  // Obtains the part-specific config for `part_name` from this RobotConfig
  // object, unpacked into a `ConfigT`. `ConfigT` must match the part's
  // `config_message_type` in its `proto::PartSignature`.
  //
  // Use this to get highly specialized information about a part. Usually,
  // `GetGenericPartConfig()` will have all information you need, though.
  template <typename ConfigT>
  absl::StatusOr<ConfigT> GetPartConfig(absl::string_view part_name) const;

  // Obtains the part-specific config for `part_name` from this RobotConfig
  // object, as a `google::protobuf::Any`. This is useful when the part's
  // config type is not known at compile-time.
  absl::StatusOr<google::protobuf::Any> GetPartConfigAny(
      absl::string_view part_name) const;

  // Obtains the list of feature interfaces implemented by part `part_name`.
  absl::StatusOr<std::vector<intrinsic_proto::icon::FeatureInterfaceTypes>>
  GetPartFeatureInterfaces(absl::string_view part_name) const;

  // Returns the ICON control frequency, in Hz.
  double GetControlFrequency() const;

  // Returns the server name that appears in logs and topic names.
  std::string_view GetServerName() const;

 private:
  absl::StatusOr<intrinsic_proto::icon::PartConfig> FindPartConfig(
      absl::string_view part_name) const;

  intrinsic_proto::icon::GetConfigResponse config_proto_;
};

//
// IMPLEMENTATION DETAILS BELOW
//

template <typename ConfigT>
absl::StatusOr<ConfigT> RobotConfig::GetPartConfig(
    absl::string_view part_name) const {
  INTRINSIC_ASSIGN_OR_RETURN(google::protobuf::Any part_config_any,
                             GetPartConfigAny(part_name));

  // Unpack to ConfigT.
  ConfigT out_proto;
  if (!part_config_any.UnpackTo(&out_proto)) {
    return absl::InvalidArgumentError(
        absl::StrCat("Failed to unpack part config for part \"", part_name,
                     "\" (did you pass the correct proto type to "
                     "`RobotConfig::GetPartConfig<ConfigT>()`?) ",
                     "part has TypeName: ", part_config_any.GetTypeName()));
  }
  return out_proto;
}

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_CC_CLIENT_ROBOT_CONFIG_H_
