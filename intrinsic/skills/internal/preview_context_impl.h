// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_PREVIEW_CONTEXT_IMPL_H_
#define INTRINSIC_SKILLS_INTERNAL_PREVIEW_CONTEXT_IMPL_H_

#include <memory>
#include <utility>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/preview_context.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_logging_context.h"
#include "intrinsic/skills/proto/prediction.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/kinematic_object.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/world_object.h"
#include "intrinsic/world/proto/object_world_updates.pb.h"

namespace intrinsic {
namespace skills {

// Implementation of PreviewContext used by the skill service.
class PreviewContextImpl : public PreviewContext {
 public:
  PreviewContextImpl(std::shared_ptr<SkillCanceller> canceller,
                     EquipmentPack equipment,
                     SkillLoggingContext logging_context,
                     motion_planning::MotionPlannerClient motion_planner,
                     world::ObjectWorldClient object_world)
      : canceller_(canceller),
        equipment_(std::move(equipment)),
        logging_context_(logging_context),
        motion_planner_(std::move(motion_planner)),
        object_world_(std::move(object_world)) {}

  SkillCanceller& canceller() const override { return *canceller_; }

  const SkillLoggingContext& logging_context() const override {
    return logging_context_;
  };

  motion_planning::MotionPlannerClient& motion_planner() override {
    return motion_planner_;
  }

  world::ObjectWorldClient& object_world() override { return object_world_; }

  const std::vector<intrinsic_proto::skills::TimedWorldUpdate>&
  GetWorldUpdates() const {
    return world_updates_;
  }

  absl::StatusOr<world::Frame> GetFrameForEquipment(
      absl::string_view equipment_name, absl::string_view frame_name) override;
  absl::StatusOr<world::KinematicObject> GetKinematicObjectForEquipment(
      absl::string_view equipment_name) override;
  absl::StatusOr<world::WorldObject> GetObjectForEquipment(
      absl::string_view equipment_name) override;

  absl::Status RecordWorldUpdate(
      const intrinsic_proto::world::ObjectWorldUpdate& update,
      absl::Duration elapsed, absl::Duration duration) override;

 private:
  std::shared_ptr<SkillCanceller> canceller_;
  EquipmentPack equipment_;
  SkillLoggingContext logging_context_;
  motion_planning::MotionPlannerClient motion_planner_;
  world::ObjectWorldClient object_world_;

  std::vector<intrinsic_proto::skills::TimedWorldUpdate> world_updates_;

  EquipmentPack& equipment() override { return equipment_; }
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_PREVIEW_CONTEXT_IMPL_H_
