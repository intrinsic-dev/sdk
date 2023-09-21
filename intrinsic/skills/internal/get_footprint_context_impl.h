// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_INTERNAL_GET_FOOTPRINT_CONTEXT_IMPL_H_
#define INTRINSIC_SKILLS_INTERNAL_GET_FOOTPRINT_CONTEXT_IMPL_H_

#include <memory>
#include <optional>
#include <string>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/skill_registry_client_interface.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic {
namespace skills {

// Implementation of GetFootprintContext as used by the skill service.
class GetFootprintContextImpl : public GetFootprintContext {
  using ObjectWorldService = ::intrinsic_proto::world::ObjectWorldService;

 public:
  GetFootprintContextImpl(
      std::string world_id,
      const intrinsic_proto::data_logger::Context& log_context,
      std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
      EquipmentPack equipment,
      SkillRegistryClientInterface& skill_registry_client);

  absl::StatusOr<world::ObjectWorldClient> GetObjectWorld() override;

  absl::StatusOr<world::KinematicObject> GetKinematicObjectForEquipment(
      absl::string_view equipment_name) override;
  absl::StatusOr<world::WorldObject> GetObjectForEquipment(
      absl::string_view equipment_name) override;
  absl::StatusOr<world::Frame> GetFrameForEquipment(
      absl::string_view equipment_name, absl::string_view frame_name) override;

 private:
  std::string world_id_;
  std::shared_ptr<ObjectWorldService::StubInterface> object_world_service_;
  EquipmentPack equipment_;
  SkillRegistryClientInterface& skill_registry_client_ ABSL_ATTRIBUTE_UNUSED;
  intrinsic_proto::data_logger::Context log_context_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_GET_FOOTPRINT_CONTEXT_IMPL_H_
