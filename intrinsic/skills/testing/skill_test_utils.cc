// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/testing/skill_test_utils.h"

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "intrinsic/skills/cc/skill_interface.h"

namespace intrinsic {
namespace skills {

absl::Status ExecuteSkill(SkillExecuteInterface& skill,
                          const ExecuteRequest& request,
                          ExecuteContext& context) {
  return skill.Execute(request, context).status();
}

absl::Status PreviewSkill(SkillExecuteInterface& skill,
                          const PreviewRequest& request,
                          PreviewContext& context) {
  return skill.Preview(request, context).status();
}

}  // namespace skills
}  // namespace intrinsic
