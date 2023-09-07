// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/internal/registerer_skill_repository.h"

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "absl/base/attributes.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/runtime_data.h"

namespace intrinsic {
namespace skills {

namespace {

// Functions must hold this mutex for the duration of reading/modifying the
// registry.
ABSL_CONST_INIT absl::Mutex skill_registry_mutex(absl::kConstInit);

using SkillRegistry = absl::flat_hash_map<
    std::string, std::function<absl::StatusOr<
                     std::unique_ptr<intrinsic::skills::SkillInterface>>()>>;

inline SkillRegistry& GetSkillRegistry() {
  skill_registry_mutex.AssertHeld();
  static auto* registry = new SkillRegistry;
  return *registry;
}

}  // namespace

absl::StatusOr<std::unique_ptr<SkillInterface>>
RegistererSkillRepository::GetSkill(absl::string_view skill_alias) {
  absl::MutexLock l(&skill_registry_mutex);
  auto& registry = GetSkillRegistry();
  if (auto iter = registry.find(skill_alias); iter != registry.end()) {
    return iter->second();
  }

  return absl::NotFoundError(absl::StrFormat(
      "did not find a skill with alias: %s; verify that the skill is registered"
      " through the 'REGISTER_SKILL' macro with the alias %s and that the "
      "skill is linked to the binary",
      skill_alias, skill_alias));
}

absl::StatusOr<std::unique_ptr<SkillExecuteInterface>>
RegistererSkillRepository::GetSkillExecute(absl::string_view skill_alias) {
  return GetSkill(skill_alias);
}

absl::StatusOr<std::unique_ptr<SkillProjectInterface>>
RegistererSkillRepository::GetSkillProject(absl::string_view skill_alias) {
  return GetSkill(skill_alias);
}

absl::StatusOr<internal::SkillRuntimeData>
RegistererSkillRepository::GetSkillRuntimeData(absl::string_view skill_alias) {
  INTRINSIC_ASSIGN_OR_RETURN(auto skill, GetSkill(skill_alias));
  return internal::GetRuntimeDataFrom(*skill);
}

std::vector<std::string> RegistererSkillRepository::GetSkillAliases() const {
  absl::MutexLock l(&skill_registry_mutex);
  return GetSkillAliasesImpl();
}

std::vector<std::string> RegistererSkillRepository::GetSkillAliasesImpl()
    const {
  skill_registry_mutex.AssertHeld();
  auto& registry = GetSkillRegistry();

  std::vector<std::string> aliases;
  aliases.reserve(registry.size());
  for (const auto& [key, _] : registry) {
    aliases.push_back(key);
  }
  return aliases;
}

int RegisterSkill(
    absl::string_view name, absl::string_view alias,
    const std::function<absl::StatusOr<std::unique_ptr<SkillInterface>>()>&
        fn) {
  absl::MutexLock l(&skill_registry_mutex);
  auto& registry = GetSkillRegistry();

  auto [_, was_inserted] = registry.insert({std::string(alias), fn});
  if (!was_inserted) {
    LOG(FATAL) << "Trying to register skill with duplicate name: " << alias;
  }
  return 0;
}

}  // namespace skills
}  // namespace intrinsic
