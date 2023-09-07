// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_EQUIPMENT_UTILITIES_H_
#define INTRINSIC_SKILLS_INTERNAL_EQUIPMENT_UTILITIES_H_

#include <string>

#include "absl/container/flat_hash_map.h"
#include "absl/status/statusor.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/footprint.pb.h"

namespace intrinsic::skills {

// Specifies equipment reservations from a Skill's EquipmentRequired
// implementation.
absl::StatusOr<google::protobuf::RepeatedPtrField<
    intrinsic_proto::skills::EquipmentResource>>
ReserveEquipmentRequired(
    const absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::EquipmentSelector>&
        equipment_required,
    const google::protobuf::Map<std::string,
                                intrinsic_proto::skills::EquipmentHandle>&
        equipment_handles);

}  // namespace intrinsic::skills

#endif  // INTRINSIC_SKILLS_INTERNAL_EQUIPMENT_UTILITIES_H_
