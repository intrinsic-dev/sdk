// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_IMPL_H_
#define INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_IMPL_H_

#include <memory>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/world/objects/object_world_client.h"

namespace intrinsic {
namespace skills {

// Implementation of ExecuteContext used by the skill service.
class ExecuteContextImpl : public ExecuteContext {
 public:
  ExecuteContextImpl(std::shared_ptr<SkillCanceller> canceller,
                     EquipmentPack equipment,
                     intrinsic_proto::data_logger::Context logging_context,
                     motion_planning::MotionPlannerClient motion_planner,
                     world::ObjectWorldClient object_world)
      : canceller_(canceller),
        equipment_(std::move(equipment)),
        logging_context_(logging_context),
        motion_planner_(std::move(motion_planner)),
        object_world_(std::move(object_world)) {}

  SkillCanceller& canceller() const override { return *canceller_; }

  const EquipmentPack& equipment() const override { return equipment_; }

  const intrinsic_proto::data_logger::Context& logging_context()
      const override {
    return logging_context_;
  }

  motion_planning::MotionPlannerClient& motion_planner() override {
    return motion_planner_;
  }

  world::ObjectWorldClient& object_world() override { return object_world_; }

 private:
  std::shared_ptr<SkillCanceller> canceller_;
  EquipmentPack equipment_;
  intrinsic_proto::data_logger::Context logging_context_;
  motion_planning::MotionPlannerClient motion_planner_;
  world::ObjectWorldClient object_world_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_EXECUTE_CONTEXT_IMPL_H_
