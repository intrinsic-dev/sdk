// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_SINGLE_SKILL_FACTORY_H_
#define INTRINSIC_SKILLS_INTERNAL_SINGLE_SKILL_FACTORY_H_

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "absl/base/thread_annotations.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/runtime_data.h"
#include "intrinsic/skills/internal/skill_repository.h"

namespace intrinsic::skills::internal {

// SingleSkillFactory implements a SkillRepository that is only able to serve
// a single skill.
class SingleSkillFactory : public SkillRepository {
 public:
  // Creates a SingleSkillFactory.
  //
  // Uses the data from `skill_runtime_data` and the `create_skill` function to
  // create new skills when requested.
  SingleSkillFactory(
      const SkillRuntimeData& skill_runtime_data,
      const std::function<absl::StatusOr<std::unique_ptr<SkillInterface>>()>&
          create_skill);

  // Not copyable or movable
  SingleSkillFactory(const SingleSkillFactory&) = delete;
  SingleSkillFactory& operator=(const SingleSkillFactory&) = delete;

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
  SkillRuntimeData skill_runtime_data_;

  std::string skill_alias_;

  absl::Mutex create_skill_mutex_;
  std::function<absl::StatusOr<std::unique_ptr<SkillInterface>>()> create_skill_
      ABSL_GUARDED_BY(create_skill_mutex_);
};

}  // namespace intrinsic::skills::internal

#endif  // INTRINSIC_SKILLS_INTERNAL_SINGLE_SKILL_FACTORY_H_
