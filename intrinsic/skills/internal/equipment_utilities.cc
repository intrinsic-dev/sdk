// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/internal/equipment_utilities.h"

#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/footprint.pb.h"

namespace intrinsic::skills {

absl::StatusOr<google::protobuf::RepeatedPtrField<
    intrinsic_proto::skills::EquipmentResource>>
ReserveEquipmentRequired(
    const absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::EquipmentSelector>&
        equipment_required,
    const google::protobuf::Map<std::string,
                                intrinsic_proto::skills::EquipmentHandle>&
        equipment_handles) {
  google::protobuf::RepeatedPtrField<intrinsic_proto::skills::EquipmentResource>
      resources;
  std::vector<std::string> missing_handles;
  for (const auto& [name, selector] : equipment_required) {
    auto handles_iter = equipment_handles.find(name);
    if (handles_iter == equipment_handles.end()) {
      missing_handles.push_back(name);
      continue;
    }
    // Handle is present so create a Resource.
    intrinsic_proto::skills::EquipmentResource resource;
    resource.set_type(selector.sharing_type());
    // `name` would be the skill internal name, but we need to reserve the
    // "external" name of the equiment.
    resource.set_name(handles_iter->second.name());
    *resources.Add() = std::move(resource);
  }
  if (!missing_handles.empty()) {
    return absl::InvalidArgumentError(
        absl::StrCat("Error when specifying equipment resources. "
                     "The Skill requires (",
                     absl::StrJoin(missing_handles, ", "),
                     ") but no handle was found with this name."));
  }
  return resources;
}

}  // namespace intrinsic::skills
