// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_INTERFACE_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_INTERFACE_H_

#include <string>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_registry_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic {
namespace skills {

// A client interface for the Skill Registry service.
class SkillRegistryClientInterface {
 public:
  virtual ~SkillRegistryClientInterface() = default;

  // Fetches all available skill interfaces.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `DeadlineExceededError` if the request hasn't completed after
  // `timeout`.
  //
  // Returns any errors from the GRPC invocation.
  //
  // Returns any errors reported in the response's `GetSkillsResponse::status`
  // field.
  virtual absl::StatusOr<std::vector<intrinsic_proto::skills::Skill>>
  GetSkills() const = 0;
  virtual absl::StatusOr<std::vector<intrinsic_proto::skills::Skill>> GetSkills(
      absl::Duration timeout) const = 0;

  // Fetches a Skill by id.
  //
  // This (indirectly) makes a blocking GRPC call.
  //
  // Returns `NotFoundError` if `skill_id` does not match a Skill in `client`.
  //
  // Returns any errors from the GRPC invocation; Returns any errors reported by
  // the Skill Registry Service.
  virtual absl::StatusOr<intrinsic_proto::skills::Skill> GetSkillById(
      absl::string_view skill_id) const = 0;

  // Fetches a skill instance matching the given request. `skill_name` is the
  // name of the skill to get an instance of. `equipment` describes which
  // equipment should be used for which equipment slots.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `DeadlineExceededError` if the request hasn't completed after
  // `timeout`.
  //
  // Returns any errors from the GRPC invocation.
  virtual absl::StatusOr<intrinsic_proto::skills::SkillInstance>
  GetInstanceByName(absl::string_view skill_name,
                    const EquipmentPack& equipment) const = 0;

  // Fetches a skill instance matching the given request. `id` is the
  // id of the skill to get an instance of. `equipment` describes which
  // equipment should be used for which equipment slots.
  //
  // This makes a blocking gRPC request.
  //
  // Returns `DeadlineExceededError` if the request hasn't completed after
  // `timeout`.
  //
  // Returns any errors from the GRPC invocation.
  virtual absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstance(
      absl::string_view id, const EquipmentPack& equipment) const = 0;
  virtual absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstance(
      absl::string_view id, const EquipmentPack& equipment,
      absl::Duration timeout) const = 0;

  // Fetches a skill instance matching the given request. `id` is the
  // id of the skill to get an instance of. `instance_id` is the name of the
  // instance and it must be unique for the lifetime of the skill registry
  // server (unless ResetInstanceIds is called). `equipment` describes which
  // equipment should be used for which equipment slots.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `DeadlineExceededError` if the request hasn't completed after
  // `timeout`.
  //
  // Returns any errors from the GRPC invocation.
  virtual absl::StatusOr<intrinsic_proto::skills::SkillInstance>
  GetInstanceWithId(absl::string_view id, absl::string_view instance_id,
                    const EquipmentPack& equipment) const = 0;
  virtual absl::StatusOr<intrinsic_proto::skills::SkillInstance>
  GetInstanceWithId(absl::string_view id, absl::string_view instance_id,
                    const EquipmentPack& equipment,
                    absl::Duration timeout) const = 0;

  // Returns the BehaviorTree that is registered for a specific skill with
  // `skill_id`. The requested skill must be a parameterizable BehaviorTree.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `DeadlineExceededError` if the request hasn't completed after
  // `timeout`.
  //
  // Returns any errors from the GRPC invocation.
  virtual absl::StatusOr<intrinsic_proto::executive::BehaviorTree>
  GetBehaviorTree(absl::string_view skill_id) const = 0;
  virtual absl::StatusOr<intrinsic_proto::executive::BehaviorTree>
  GetBehaviorTree(absl::string_view skill_id, absl::Duration timeout) const = 0;

  // Registers a new skill (or updates an existing one). Skill registrations are
  // stored and retrieved by their skill name. If the registry already has a
  // skill registered by skill name then this call will update its registration.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `FailedPreconditionError` if the registration is invalid.
  //
  // Returns any errors from the GRPC invocation; Returns any errors reported by
  // the Skill Registry Service.
  virtual absl::Status RegisterOrUpdateSkill(
      intrinsic_proto::skills::SkillRegistration skill_registration) const = 0;
  virtual absl::Status RegisterOrUpdateSkill(
      intrinsic_proto::skills::SkillRegistration skill_registration,
      absl::Duration timeout) const = 0;

  // Registers a BehaviorTree (or updates an existing one) in the skill
  // registry. The BehaviorTree is registered by its skill description's skill
  // id. If the registry already has a behavior tree registered by the skill id
  // then this call will update its registration.
  //
  // This makes a blocking GRPC request.
  //
  // Returns `FailedPreconditionError` if the registration is invalid.
  //
  // Returns any errors from the GRPC invocation; Returns any errors reported by
  // the Skill Registry Service.
  virtual absl::Status RegisterOrUpdateBehaviorTree(
      intrinsic_proto::skills::BehaviorTreeRegistration
          behavior_tree_registration) const = 0;
  virtual absl::Status RegisterOrUpdateBehaviorTree(
      intrinsic_proto::skills::BehaviorTreeRegistration
          behavior_tree_registration,
      absl::Duration timeout) const = 0;

  // Resets the set of already-used instance ids. This allows clients to reuse
  // an instance id that has already been assigned.
  //
  // This makes a blocking GRPC request.
  //
  // Returns any errors from the GRPC invocation; Returns any errors reported by
  // the Skill Registry Service.
  virtual absl::Status ResetInstanceIds() const = 0;
  virtual absl::Status ResetInstanceIds(absl::Duration timeout) const = 0;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_INTERFACE_H_
