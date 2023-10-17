// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_REGISTERER_SKILL_REPOSITORY_H_
#define INTRINSIC_SKILLS_INTERNAL_REGISTERER_SKILL_REPOSITORY_H_

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/runtime_data.h"
#include "intrinsic/skills/internal/skill_repository.h"

namespace intrinsic {
namespace skills {

// Implementation of SkillRepository that provides access to all skills which
// are registered with the REGISTER_SKILL(...) macro and which are linked to the
// current process.
class RegistererSkillRepository : public SkillRepository {
 public:
  // Constructs a new skill on each call from the factory function provided when
  // the Skill was registered via REGISTER_SKILL(...).
  absl::StatusOr<std::unique_ptr<SkillInterface>> GetSkill(
      absl::string_view skill_alias) override;

  std::vector<std::string> GetSkillAliases() const override;

  absl::StatusOr<std::unique_ptr<SkillExecuteInterface>> GetSkillExecute(
      absl::string_view skill_alias) override;

  absl::StatusOr<std::unique_ptr<SkillProjectInterface>> GetSkillProject(
      absl::string_view skill_alias) override;

  absl::StatusOr<internal::SkillRuntimeData> GetSkillRuntimeData(
      absl::string_view skill_alias) override;

 private:
  std::vector<std::string> GetSkillAliasesImpl() const;
};

int RegisterSkill(
    absl::string_view name, absl::string_view alias,
    const std::function<absl::StatusOr<std::unique_ptr<SkillInterface>>()>& fn);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_REGISTERER_SKILL_REPOSITORY_H_
