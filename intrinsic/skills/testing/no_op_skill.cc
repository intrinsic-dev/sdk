// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/testing/no_op_skill.h"

#include <memory>
#include <string>

#include "absl/container/flat_hash_map.h"
#include "absl/status/statusor.h"
#include "google/protobuf/descriptor.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/cc/skill_registration.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/testing/no_op_skill.pb.h"

namespace intrinsic::skills {

std::unique_ptr<SkillInterface> NoOpSkill::CreateSkill() {
  return std::make_unique<NoOpSkill>();
}

std::string NoOpSkill::Name() const { return "no_op"; }

absl::flat_hash_map<std::string, intrinsic_proto::skills::EquipmentSelector>
NoOpSkill::EquipmentRequired() const {
  return {};
}

const google::protobuf::Descriptor* NoOpSkill::GetParameterDescriptor() const {
  return intrinsic_proto::skills::NoOpSkillParams::descriptor();
}

absl::StatusOr<intrinsic_proto::skills::ExecuteResult> NoOpSkill::Execute(
    const ExecuteRequest& request, ExecuteContext& context) {
  return intrinsic_proto::skills::ExecuteResult();
}

REGISTER_SKILL(NoOpSkill, "no_op", NoOpSkill::CreateSkill);

}  // namespace intrinsic::skills
