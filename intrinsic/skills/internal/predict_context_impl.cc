// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/internal/predict_context_impl.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "google/protobuf/message.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/skills/internal/default_parameters.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic {
namespace skills {

using ::intrinsic::world::ObjectWorldClient;

PredictContextImpl::PredictContextImpl(
    std::string world_id,
    const intrinsic_proto::data_logger::Context& log_context,
    std::shared_ptr<ObjectWorldService::StubInterface> object_world_service,
    std::shared_ptr<MotionPlannerService::StubInterface> motion_planner_service,
    EquipmentPack equipment,
    SkillRegistryClientInterface& skill_registry_client)
    : world_id_(std::move(world_id)),
      object_world_service_(std::move(object_world_service)),
      motion_planner_service_(std::move(motion_planner_service)),
      equipment_(std::move(equipment)),
      skill_registry_client_(skill_registry_client),
      log_context_(log_context) {}

absl::StatusOr<const ObjectWorldClient> PredictContextImpl::GetObjectWorld() {
  return ObjectWorldClient(world_id_, object_world_service_);
}

absl::StatusOr<const world::KinematicObject>
PredictContextImpl::GetKinematicObjectForEquipment(
    absl::string_view equipment_name) {
  INTRINSIC_ASSIGN_OR_RETURN(const ObjectWorldClient& world, GetObjectWorld());
  INTRINSIC_ASSIGN_OR_RETURN(
      const intrinsic_proto::skills::EquipmentHandle handle,
      equipment_.GetHandle(equipment_name));
  return world.GetKinematicObject(handle);
}

absl::StatusOr<const world::WorldObject>
PredictContextImpl::GetObjectForEquipment(absl::string_view equipment_name) {
  INTRINSIC_ASSIGN_OR_RETURN(const ObjectWorldClient& world, GetObjectWorld());
  INTRINSIC_ASSIGN_OR_RETURN(
      const intrinsic_proto::skills::EquipmentHandle handle,
      equipment_.GetHandle(equipment_name));
  return world.GetObject(handle);
}

absl::StatusOr<const world::Frame> PredictContextImpl::GetFrameForEquipment(
    absl::string_view equipment_name, absl::string_view frame_name) {
  INTRINSIC_ASSIGN_OR_RETURN(const ObjectWorldClient& world, GetObjectWorld());
  INTRINSIC_ASSIGN_OR_RETURN(
      const intrinsic_proto::skills::EquipmentHandle handle,
      equipment_.GetHandle(equipment_name));
  return world.GetFrame(handle, FrameName(frame_name));
}

absl::StatusOr<motion_planning::MotionPlannerClient>
PredictContextImpl::GetMotionPlanner() {
  return motion_planning::MotionPlannerClient(world_id_,
                                              motion_planner_service_);
}

}  // namespace skills
}  // namespace intrinsic
