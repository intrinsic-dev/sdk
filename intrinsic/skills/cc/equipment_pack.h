// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_EQUIPMENT_PACK_H_
#define INTRINSIC_SKILLS_CC_EQUIPMENT_PACK_H_

#include <string>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"

namespace intrinsic {
namespace skills {

// Provides easy access to the contents of a proto::ResourceHandle map, based
// on the equipment key.
class EquipmentPack {
 private:
  using EquipmentMap =
      absl::flat_hash_map<std::string, intrinsic_proto::skills::ResourceHandle>;
  using EquipmentIterator = EquipmentMap::const_iterator;

 public:
  EquipmentPack() = default;
  explicit EquipmentPack(const google::protobuf::Map<
                         std::string, intrinsic_proto::skills::ResourceHandle>&
                             resource_handles);

  static absl::StatusOr<EquipmentPack> GetEquipmentPack(
      const intrinsic_proto::skills::PredictRequest& request);

  static absl::StatusOr<EquipmentPack> GetEquipmentPack(
      const intrinsic_proto::skills::GetFootprintRequest& request);

  static absl::StatusOr<EquipmentPack> GetEquipmentPack(
      const intrinsic_proto::skills::ExecuteRequest& request);

  static absl::StatusOr<EquipmentPack> GetEquipmentPack(
      const intrinsic_proto::skills::PreviewRequest& request);

  // Unpacks the contents of the equipment at `key`.
  // returns failure if the `key` does not exist or the EquipmentType does not
  //    match the content type at the `key`.
  template <typename EquipmentType>
  absl::StatusOr<EquipmentType> Unpack(absl::string_view key,
                                       absl::string_view type) const;

  // Returns the resource handle itself for the given key. This is useful if
  // you need something other than the content of the equipment.
  absl::StatusOr<intrinsic_proto::skills::ResourceHandle> GetHandle(
      absl::string_view key) const;

  // Removes the resource handle from this equipment pack by key.
  absl::Status Remove(absl::string_view key);

  // Adds the resource handle to this equipment pack.
  absl::Status Add(absl::string_view key,
                   intrinsic_proto::skills::ResourceHandle handle);

  // Allow const iteration through the resource handles.
  EquipmentIterator begin() const { return equipment_map_.begin(); }
  EquipmentIterator end() const { return equipment_map_.end(); }

 private:
  EquipmentMap equipment_map_;
};

namespace internal {

absl::Status MissingEquipmentError(absl::string_view key);
absl::Status EquipmentContentsTypeError();

}  // namespace internal

template <typename EquipmentType>
absl::StatusOr<EquipmentType> EquipmentPack::Unpack(
    absl::string_view key, absl::string_view type) const {
  if (!equipment_map_.contains(key)) {
    return internal::MissingEquipmentError(key);
  }

  const auto& resource_data = equipment_map_.at(key).resource_data();
  if (!resource_data.contains(std::string(type))) {
    return absl::NotFoundError(absl::StrCat("Could not find equipment typed '",
                                            type, "' with slot key '", key,
                                            "'"));
  }

  EquipmentType equipment;
  if (!resource_data.at(std::string(type)).contents().UnpackTo(&equipment)) {
    return internal::EquipmentContentsTypeError();
  }

  return equipment;
}

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_EQUIPMENT_PACK_H_
