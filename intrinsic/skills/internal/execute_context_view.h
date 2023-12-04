// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_VIEW_H_
#define INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_VIEW_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/cc/skill_logging_context.h"
#include "intrinsic/world/objects/object_world_client.h"

namespace intrinsic {
namespace skills {

// ExecuteContext that just stores references to the objects it provides.
//
// Can be used when an ExecuteContext is needed and the objects it provides are
// owned by some other object (such as a PreviewContext).
class ExecuteContextView : public ExecuteContext {
 public:
  ExecuteContextView(SkillCanceller& canceller, const EquipmentPack& equipment,
                     const SkillLoggingContext& logging_context,
                     motion_planning::MotionPlannerClient& motion_planner,
                     world::ObjectWorldClient& object_world)
      : canceller_(canceller),
        equipment_(equipment),
        logging_context_(logging_context),
        motion_planner_(motion_planner),
        object_world_(object_world) {}

  SkillCanceller& canceller() const override { return canceller_; }

  const EquipmentPack& equipment() const override { return equipment_; }

  const SkillLoggingContext& logging_context() const override {
    return logging_context_;
  }

  motion_planning::MotionPlannerClient& motion_planner() override {
    return motion_planner_;
  }

  world::ObjectWorldClient& object_world() override { return object_world_; }

 private:
  SkillCanceller& canceller_;
  const EquipmentPack& equipment_;
  const SkillLoggingContext& logging_context_;
  motion_planning::MotionPlannerClient& motion_planner_;
  world::ObjectWorldClient& object_world_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_VIEW_H_
