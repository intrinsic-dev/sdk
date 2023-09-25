// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/cc/equipment_pack.h"

#include <string>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic {
namespace skills {

EquipmentPack::EquipmentPack(
    const google::protobuf::Map<std::string,
                                intrinsic_proto::skills::EquipmentHandle>&
        equipment_handles)
    : equipment_map_(equipment_handles.begin(), equipment_handles.end()) {}

absl::StatusOr<EquipmentPack> EquipmentPack::GetEquipmentPack(
    const intrinsic_proto::skills::PredictRequest& request) {
  if (!request.has_instance()) {
    return absl::InvalidArgumentError(
        "In `request`, expected a skill `instance`, but the `instance` is "
        "missing.");
  }
  return EquipmentPack(request.instance().equipment_handles());
}

absl::StatusOr<EquipmentPack> EquipmentPack::GetEquipmentPack(
    const intrinsic_proto::skills::GetFootprintRequest& request) {
  if (!request.has_instance()) {
    return absl::InvalidArgumentError(
        "In `request`, expected a skill `instance`, but the `instance` is "
        "missing.");
  }
  return EquipmentPack(request.instance().equipment_handles());
}

absl::StatusOr<EquipmentPack> EquipmentPack::GetEquipmentPack(
    const intrinsic_proto::skills::ExecuteRequest& request) {
  if (!request.has_instance()) {
    return absl::InvalidArgumentError(
        "In `request`, expected a skill `instance`, but the `instance` is "
        "missing.");
  }
  return EquipmentPack(request.instance().equipment_handles());
}

absl::StatusOr<intrinsic_proto::skills::EquipmentHandle>
EquipmentPack::GetHandle(absl::string_view key) const {
  if (!equipment_map_.contains(key)) {
    return internal::MissingEquipmentError(key);
  }

  return equipment_map_.at(key);
}

absl::Status EquipmentPack::Remove(absl::string_view key) {
  if (equipment_map_.erase(key) == 0) {
    return internal::MissingEquipmentError(key);
  }
  return absl::OkStatus();
}

absl::Status EquipmentPack::Add(
    absl::string_view key, intrinsic_proto::skills::EquipmentHandle handle) {
  if (equipment_map_.contains(key)) {
    return absl::InvalidArgumentError(
        absl::StrCat("Equipment pack already contains handle for key: ", key));
  }

  equipment_map_[key] = handle;
  return absl::OkStatus();
}

namespace internal {

absl::Status MissingEquipmentError(absl::string_view key) {
  return {absl::StatusCode::kInvalidArgument,
          absl::StrCat("Missing equipment handle for slot: ", key)};
}

absl::Status EquipmentContentsTypeError() {
  return {absl::StatusCode::kInvalidArgument,
          "Failed to unpack Any proto into `equipment`. "
          "Maybe the given `equipment` is of an incorrect protobuf::Message "
          "type?"};
}

}  // namespace internal

}  // namespace skills
}  // namespace intrinsic
