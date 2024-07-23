// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_CONFIG_UTILS_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_CONFIG_UTILS_H_

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"

namespace intrinsic::skills {

// Returns the SkillServiceConfig at `skill_service_config_filename`.
//
// Reads the proto binary file at `skill_service_config_filename` and returns
// the contents. This file must contain a proto binary
// intrinsic_proto.skills.SkillServiceConfig message.
absl::StatusOr<intrinsic_proto::skills::SkillServiceConfig>
GetSkillServiceConfig(absl::string_view skill_service_config_filename);

}  // namespace intrinsic::skills

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_SERVICE_CONFIG_UTILS_H_
