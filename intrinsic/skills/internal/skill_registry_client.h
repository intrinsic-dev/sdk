// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "grpcpp/grpcpp.h"
#include "grpcpp/impl/channel_interface.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/internal/proto/behavior_tree_registry_internal.grpc.pb.h"
#include "intrinsic/skills/internal/proto/skill_registry_internal.grpc.pb.h"
#include "intrinsic/skills/internal/skill_registry_client_interface.h"
#include "intrinsic/skills/proto/behavior_tree_registry.grpc.pb.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_registry.grpc.pb.h"
#include "intrinsic/skills/proto/skill_registry_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic {
namespace skills {

// This header defines the Skills Registry C++ client library, which is a thin
// wrapper around the Skills Registry GRPC API.

class SkillRegistryClient;

// Creates a client that connects to the Skill Registry GRPC service at address
// `grpc_address`.
absl::StatusOr<std::unique_ptr<SkillRegistryClient>> CreateSkillRegistryClient(
    absl::string_view grpc_address,
    absl::Duration timeout = intrinsic::kGrpcClientConnectDefaultTimeout);

// A client for the Skill Registry service.
//
// This object is moveable but not copyable.
class SkillRegistryClient : public SkillRegistryClientInterface {
 public:
  // Constructs a Skill Registry client that wraps `stub`.
  explicit SkillRegistryClient(
      std::unique_ptr<
          intrinsic_proto::skills::SkillRegistryInternal::StubInterface>
          stub_internal,
      std::unique_ptr<intrinsic_proto::skills::SkillRegistry::StubInterface>
          stub,
      std::unique_ptr<
          intrinsic_proto::skills::BehaviorTreeRegistryInternal::StubInterface>
          bt_stub_internal,
      std::unique_ptr<
          intrinsic_proto::skills::BehaviorTreeRegistry::StubInterface>
          bt_stub)
      : stub_internal_(std::move(stub_internal)),
        stub_(std::move(stub)),
        bt_stub_internal_(std::move(bt_stub_internal)),
        bt_stub_(std::move(bt_stub)) {}

  absl::StatusOr<std::vector<intrinsic_proto::skills::Skill>> GetSkills()
      const final;

  absl::StatusOr<std::vector<intrinsic_proto::skills::Skill>> GetSkills(
      absl::Duration timeout) const final;

  absl::StatusOr<intrinsic_proto::skills::Skill> GetSkillById(
      absl::string_view skill_id) const final;

  absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstance(
      absl::string_view id, const EquipmentPack& equipment) const final;

  absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstance(
      absl::string_view id, const EquipmentPack& equipment,
      absl::Duration timeout) const final;

  absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstanceWithId(
      absl::string_view id, absl::string_view instance_id,
      const EquipmentPack& equipment) const final;

  absl::StatusOr<intrinsic_proto::skills::SkillInstance> GetInstanceWithId(
      absl::string_view id, absl::string_view instance_id,
      const EquipmentPack& equipment, absl::Duration timeout) const final;

  absl::StatusOr<intrinsic_proto::executive::BehaviorTree> GetBehaviorTree(
      absl::string_view skill_id) const final;
  absl::StatusOr<intrinsic_proto::executive::BehaviorTree> GetBehaviorTree(
      absl::string_view skill_id, absl::Duration timeout) const final;

  absl::Status RegisterOrUpdateSkill(intrinsic_proto::skills::SkillRegistration
                                         skill_registration) const final;
  absl::Status RegisterOrUpdateSkill(
      intrinsic_proto::skills::SkillRegistration skill_registration,
      absl::Duration timeout) const final;

  absl::Status RegisterOrUpdateBehaviorTree(
      intrinsic_proto::skills::BehaviorTreeRegistration
          behavior_tree_registration) const final;
  absl::Status RegisterOrUpdateBehaviorTree(
      intrinsic_proto::skills::BehaviorTreeRegistration
          behavior_tree_registration,
      absl::Duration timeout) const final;

  absl::Status ResetInstanceIds() const final;
  absl::Status ResetInstanceIds(absl::Duration timeout) const final;

 private:
  std::shared_ptr<::grpc::ChannelInterface> channel_;
  std::unique_ptr<intrinsic_proto::skills::SkillRegistryInternal::StubInterface>
      stub_internal_;
  std::unique_ptr<intrinsic_proto::skills::SkillRegistry::StubInterface> stub_;
  std::unique_ptr<
      intrinsic_proto::skills::BehaviorTreeRegistryInternal::StubInterface>
      bt_stub_internal_;
  std::unique_ptr<intrinsic_proto::skills::BehaviorTreeRegistry::StubInterface>
      bt_stub_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_REGISTRY_CLIENT_H_
