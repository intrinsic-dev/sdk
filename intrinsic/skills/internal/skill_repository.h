// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_REPOSITORY_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_REPOSITORY_H_

#include <memory>
#include <string>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/runtime_data.h"

namespace intrinsic {
namespace skills {

// Provides access to a collection of skills identified by their skill aliases.
//
// Implementations of this class should be thread-safe and expect that all
// methods may be called concurrently without external synchronization.
class SkillRepository {
 public:
  virtual ~SkillRepository() = default;

  // Returns the skill interface corresponding to the provided alias.
  //
  // Implementations may differ in how a skill interface is produced on each
  // call with the following contract: For repeated calls with the same alias,
  // implementations always have to:
  //
  // - return the same implementation of SkillInterface
  // - and return completely independent objects (e.g., by creating new
  //    instances on every call),
  // - or return an error if no new object can be provided.
  //
  //  See the derived classes for additional information.
  virtual absl::StatusOr<std::unique_ptr<SkillInterface>> GetSkill(
      absl::string_view skill_alias) = 0;

  virtual absl::StatusOr<std::unique_ptr<SkillExecuteInterface>>
  GetSkillExecute(absl::string_view skill_alias) = 0;

  virtual absl::StatusOr<std::unique_ptr<SkillProjectInterface>>
  GetSkillProject(absl::string_view skill_alias) = 0;

  virtual absl::StatusOr<internal::SkillRuntimeData> GetSkillRuntimeData(
      absl::string_view skill_alias) = 0;

  // Returns the aliases of all Skills registered to this repository.
  virtual std::vector<std::string> GetSkillAliases() const = 0;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_REPOSITORY_H_
