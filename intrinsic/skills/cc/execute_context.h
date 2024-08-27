// Copyright 2023 Intrinsic Innovation LLC


#ifndef INTRINSIC_SKILLS_CC_EXECUTE_CONTEXT_H_
#define INTRINSIC_SKILLS_CC_EXECUTE_CONTEXT_H_

#include <memory>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "grpcpp/channel.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_logging_context.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/world/objects/object_world_client.h"

namespace intrinsic {
namespace skills {

// Provides extra metadata and functionality for a Skill::Execute call.
//
// It is provided by the skill service to a skill and allows access to the world
// and other services that a skill may use.

// ExecuteContext helps support cooperative skill cancellation via a
// SkillCanceller. When a cancellation request is received, the skill should:
// 1) stop as soon as possible and leave resources in a safe and recoverable
//    state;
// 2) return absl::CancelledError.
class ExecuteContext {
 public:
  virtual ~ExecuteContext() = default;

  // Supports cooperative cancellation of the skill.
  virtual SkillCanceller& canceller() const = 0;

  // Equipment mapping associated with this skill instance.
  virtual const EquipmentPack& equipment() const = 0;

  // The logging context of the execution.
  virtual const SkillLoggingContext& logging_context() const = 0;

  // A client for the motion planning service.
  virtual motion_planning::MotionPlannerClient& motion_planner() = 0;

  // A client for interacting with the object world.
  virtual world::ObjectWorldClient& object_world() = 0;

 protected:
  // Returns a `grpc::Channel` that can be used to connect to the World service.
  // This is intended for internal use. Use object_world() instead.
  virtual absl::StatusOr<std::shared_ptr<grpc::Channel>> GetWorldChannel()
      const {
    return absl::UnimplementedError(
        "GetWorldChannel is not intended for public use.");
  }
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_EXECUTE_CONTEXT_H_
