// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_GET_FOOTPRINT_CONTEXT_H_
#define INTRINSIC_SKILLS_CC_GET_FOOTPRINT_CONTEXT_H_

#include "absl/log/check.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/proto/footprint.pb.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/kinematic_object.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/world_object.h"

namespace intrinsic {
namespace skills {

// Provides extra metadata and functionality for a Skill::GetFootprint call.
//
// It is provided by the skill service to a skill and allows access to the world
// and other services that a skill may use.
class GetFootprintContext {
 public:
  virtual ~GetFootprintContext() = default;

  // A client for the motion planning service.
  virtual motion_planning::MotionPlannerClient& motion_planner() = 0;

  // A client for interacting with the object world.
  virtual world::ObjectWorldClient& object_world() = 0;

  // Returns the frame by name for an object corresponding to some equipment.
  //
  // The frame is sourced from the same world that's available via
  // object_world().
  virtual absl::StatusOr<world::Frame> GetFrameForEquipment(
      absl::string_view equipment_name, absl::string_view frame_name) = 0;

  // Returns the kinematic object that corresponds to this equipment.
  //
  // The kinematic object is sourced from the same world that's available via
  // object_world().
  virtual absl::StatusOr<world::KinematicObject> GetKinematicObjectForEquipment(
      absl::string_view equipment_name) = 0;

  // Returns the world object that corresponds to this equipment.
  //
  // The world object is sourced from the same world that's available via
  // object_world().
  virtual absl::StatusOr<world::WorldObject> GetObjectForEquipment(
      absl::string_view equipment_name) = 0;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_GET_FOOTPRINT_CONTEXT_H_
