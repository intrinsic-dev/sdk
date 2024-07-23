// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/internal/skill_service_config_utils.h"

#include "absl/log/log.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::skills {

absl::StatusOr<intrinsic_proto::skills::SkillServiceConfig>
GetSkillServiceConfig(absl::string_view skill_service_config_filename) {
  intrinsic_proto::skills::SkillServiceConfig service_config;
  if (!skill_service_config_filename.empty()) {
    LOG(INFO) << "Reading skill configuration proto from "
              << skill_service_config_filename;
    INTR_ASSIGN_OR_RETURN(
        service_config,
        intrinsic::GetBinaryProto<intrinsic_proto::skills::SkillServiceConfig>(
            skill_service_config_filename));
    LOG(INFO) << "\nUsing skill configuration proto:\n" << service_config;
  }
  return service_config;
}

}  // namespace intrinsic::skills
