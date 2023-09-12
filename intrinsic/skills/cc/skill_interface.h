// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_
#define INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_

#include <cstddef>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/functional/any_invocable.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/client_common.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/footprint.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/world/objects/object_world_client.h"

namespace intrinsic {
namespace skills {

// Interface definition of Skill signature that includes the name, and
// input / output parameter types.
class SkillSignatureInterface {
 public:
  // Returns the name of the Skill. The name must be unique amongst all Skills.
  //
  // This name will be used to invoke the skill in a notebook or behavior tree.
  virtual std::string Name() const {
    // Not using QCHECK so that users can see what triggered the error.
    CHECK(false)
        << "Name() is not overridden but is invoked. If you're implementing a "
           "new skill, implement your skill with a manifest.";
    return "unnamed";
  }

  // The package name for the skill.
  virtual std::string Package() const { return ""; }

  // Returns a string that describes the Skill.
  //
  // This documentation string is displayed to application authors.
  //
  // Note: Documentation for parameters should be provided inline with the
  // parameter message for the skill.
  virtual std::string DocString() const { return ""; }

  // Returns a map of required equipment for the Skill.
  //
  // This is used to defined the types of equipment supported by the skill.
  //
  // The keys of this map are the name of the 'slot' for the equipment, and the
  // values are the `EquipmentSelector`s corresponding to each 'slot'. The
  // `EquipmentSelector`s describe the type of equipment required for the slot.
  virtual absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::EquipmentSelector>
  EquipmentRequired() const {
    return {};
  }

  // Returns a non-owning pointer to the Descriptor for the parameter message of
  // this Skill.
  //
  // This associates the parameter message defined for the skill with the Skill.
  // Every Skill must provide a parameter message, even if the message is empty.
  virtual const google::protobuf::Descriptor* GetParameterDescriptor() const {
    CHECK(false)
        << "GetParameterDescriptor() is not overridden but is invoked. "
           "If you're implementing a new skill, implement your skill with a "
           "manifest.";
    return nullptr;
  }

  // Returns a message containing the default parameters for the Skill. These
  // will be applied by the Skill server if the parameters are not explicitly
  // set when the skill is invoked (projected or executed).
  //
  // Fields with default parameters must be marked as `optional` in the proto
  // schema.
  virtual std::unique_ptr<google::protobuf::Message> GetDefaultParameters()
      const {
    return nullptr;
  }

  // Returns a non-owning pointer to the Descriptor for the return value message
  // of this Skill.
  //
  // This associates the return value message defined for the skill with the
  // Skill.
  virtual const google::protobuf::Descriptor* GetReturnValueDescriptor() const {
    return nullptr;
  }

  // Returns true if the skill supports cancellation.
  virtual bool SupportsCancellation() const { return false; }

  // Returns the skill's ready for cancellation timeout.
  //
  // If the skill is cancelled, its ExecuteContext waits for at most this
  // timeout duration for the skill to have called `NotifyReadyForCancellation`
  // before raising a timeout error.
  virtual absl::Duration GetReadyForCancellationTimeout() const {
    return absl::Seconds(30);
  }

  virtual ~SkillSignatureInterface() = default;
};

// Contains additional metadata and functionality for a skill projection that is
// provided by the skill service server to a skill. Allows, e.g., to read the
// world.
class ProjectionContext {
 public:
  virtual ~ProjectionContext() = default;

  // Returns the object-based view of the world associated with the skill
  // projection so that the skill can read it.
  //
  // Note, it is impossible to unwrap a StatusOr<const T> into a const T,
  // because const variables are not movable. However, it is possible to unwrap
  // a StatusOr<const T> into a const T&, since const refs extend the lifetime
  // of temporary objects. Hence, the following is the recommended usage of this
  // function:
  //   INTRINSIC_ASSIGN_OR_RETURN(const world::ObjectWorldClient& world,
  //                    context.GetObjectWorld());
  virtual absl::StatusOr<const world::ObjectWorldClient> GetObjectWorld() = 0;

  // Returns the world id of the world associated with the skill projection.
  virtual std::string GetWorldId() const = 0;

  // Returns the world object that represents the equipment in the world as
  // required by the skill within this context.
  virtual absl::StatusOr<const world::KinematicObject>
  GetKinematicObjectForEquipment(absl::string_view equipment_name) = 0;
  virtual absl::StatusOr<const world::WorldObject> GetObjectForEquipment(
      absl::string_view equipment_name) = 0;
  virtual absl::StatusOr<const world::Frame> GetFrameForEquipment(
      absl::string_view equipment_name, absl::string_view frame_name) = 0;

  // Returns a motion planner based on the world associated with the skill
  // projection (see GetObjectWorld()).
  virtual absl::StatusOr<motion_planning::MotionPlannerClient>
  GetMotionPlanner() = 0;
};

// Interface definition of Skill projecting.
class SkillProjectInterface {
 public:
  using ProjectRequest = intrinsic_proto::skills::ProjectRequest;
  using ProjectResult = intrinsic_proto::skills::ProjectResult;
  using PredictResult = intrinsic_proto::skills::PredictResult;

  struct ProjectParams {
    // The skill parameters for computing potential behavior
    google::protobuf::Any skill_parameters;

    // Any useful internal data from previous calls to the SkillProjectInterface
    std::string internal_data;
  };

  // Computes the skill's footprint. `world` contains the world under which the
  // skill is expected to operate, and this function should not modify it.
  virtual absl::StatusOr<ProjectResult> GetFootprint(
      const ProjectParams& params, ProjectionContext& context) const {
    ProjectResult result;
    result.set_internal_data(params.internal_data.data(),
                             params.internal_data.size());
    result.mutable_footprint()->set_lock_the_universe(true);
    return std::move(result);
  }

  // Generates a distribution of possible outcomes from running this skill with
  // the provided parameters.
  virtual absl::StatusOr<PredictResult> Predict(
      const ProjectParams& params, ProjectionContext& context) const {
    return absl::UnimplementedError("No user-defined call for Predict()");
  }

  virtual ~SkillProjectInterface() = default;
};

// Contains additional metadata and functionality for a skill execution that is
// provided by the skill service server to a skill. Allows, e.g., to modify the
// world or to invoke subskills.
//
// ExecuteContext helps support cooperative skill cancellation. When a
// cancellation request is received, the skill should stop as soon as possible
// and leave resources in a safe and recoverable state.
//
// If a skill supports cancellation, it must notify its ExecuteContext via
// `NotifyReadyForCancellation` once it is ready to be cancelled.
//
// A skill can implement cancellation in one of two ways:
// 1) Poll Cancelled(), and safely cancel the operation if and when it returns
//    true.
// 2) Register a cancellation callback via `RegisterCancellationCallback`. This
//    callback will be invoked when the skill receives a cancellation request.
class ExecuteContext {
 public:
  // Returns the log context this skill is called with. It includes logging IDs
  // from the higher stack.
  virtual const intrinsic_proto::data_logger::Context& GetLogContext()
      const = 0;

  // Returns the object-based view of the world associated with the current
  // execution so that the skill can query and modify it.
  virtual absl::StatusOr<world::ObjectWorldClient> GetObjectWorld() = 0;

  // Returns a motion planner based on the world associated with the current
  // execution (see GetObjectWorld()).
  virtual absl::StatusOr<motion_planning::MotionPlannerClient>
  GetMotionPlanner() = 0;

  // Notifies the context that the skill is ready to be cancelled.
  virtual void NotifyReadyForCancellation() = 0;

  // Returns true if the skill framework has received a cancellation request.
  virtual bool Cancelled() = 0;

  // Sets a callback that will be invoked when a cancellation is requested.
  //
  // If a callback will be used, it must be registered before calling
  // `NotifyReadyForCancellation`. Only one callback may be registered, and the
  // callback will be called at most once.
  virtual absl::Status RegisterCancellationCallback(
      absl::AnyInvocable<absl::Status() const> cb) = 0;

  // Returns the equipment mapping associated with this skill instance.
  virtual const EquipmentPack& GetEquipment() const = 0;

  virtual ~ExecuteContext() = default;
};

// Interface for Skill execution.
class SkillExecuteInterface {
 public:
  // Executes the skill. `context` provides access to the world and other
  // services that a skill may use.
  //
  // The skill should return an error if execution failed, and otherwise an
  // ExecuteResult. This result is typically empty, but may be populated with
  // arbitrary data in the `result` field.
  //
  // Implementations that support cancellation should return
  // absl::CancelledError if the skill is aborted due to a cancellation request.
  virtual absl::StatusOr<intrinsic_proto::skills::ExecuteResult> Execute(
      const intrinsic_proto::skills::ExecuteRequest& execute_request,
      ExecuteContext& context) {
    return absl::UnimplementedError("Skill does not implement execution.");
  }

  virtual ~SkillExecuteInterface() = default;
};

// Interface that combines all constituents of a skill.
// - SkillSignatureInterface: Name and Input parameters.
// - SkillExecuteInterface: Skill execution with provided parameters.
//
// If a skill implementation supports cancellation, it should:
// 1) Stop as soon as possible and leave resources in a safe and recoverable
//   state when a cancellation request is received (via its ExecuteContext).
// 2) Override `SupportsCancellation` to return true.
class SkillInterface : public SkillSignatureInterface,
                       public SkillProjectInterface,
                       public SkillExecuteInterface {
 public:
  ~SkillInterface() override = default;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_
