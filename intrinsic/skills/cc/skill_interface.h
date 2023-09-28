// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_
#define INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/message.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/skills/cc/client_common.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/internal/default_parameters.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/footprint.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"
#include "intrinsic/world/objects/frame.h"
#include "intrinsic/world/objects/kinematic_object.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/objects/world_object.h"

namespace intrinsic {
namespace skills {

namespace internal {

template <class TMsg>
absl::StatusOr<TMsg> ResolveParams(
    const ::google::protobuf::Any& params_any,
    const std::optional<::google::protobuf::Any>& defaults_any);

}  // namespace internal

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
  // timeout duration for the skill to have called SkillCanceller::Ready()
  // before raising a timeout error.
  virtual absl::Duration GetReadyForCancellationTimeout() const {
    return absl::Seconds(30);
  }

  virtual ~SkillSignatureInterface() = default;
};

// A request for a call to SkillInterface::GetFootprint.
class GetFootprintRequest {
 public:
  // As a convenience, `param_defaults` can specify default parameter values to
  // merge into any unset fields of `params`.
  GetFootprintRequest(const ::google::protobuf::Message& params,
                      ::google::protobuf::Message* param_defaults = nullptr) {
    params_any_.PackFrom(params);
    if (param_defaults != nullptr) {
      param_defaults_any_ = google::protobuf::Any();
      param_defaults_any_->PackFrom(*param_defaults);
    }
  }

  // Defers conversion of input Any params to target proto type until accessed
  // by the user in params().
  //
  // This constructor enables conversion from Any to the target type without
  // needing a message pool/factory up front, since params() is templated on the
  // target type.
  GetFootprintRequest(google::protobuf::Any params,
                      std::optional<::google::protobuf::Any> param_defaults)
      :  //
        params_any_(std::move(params)),
        param_defaults_any_(std::move(param_defaults)) {}

  // The skill parameters proto.
  template <class TParams>
  absl::StatusOr<TParams> params() const {
    return internal::ResolveParams<TParams>(params_any_, param_defaults_any_);
  }

 private:
  ::google::protobuf::Any params_any_;
  std::optional<::google::protobuf::Any> param_defaults_any_;
};

// Contains additional metadata and functionality for a skill footprint that is
// provided by the skill service to a skill. Allows, e.g., to read the
// world.
class GetFootprintContext {
 public:
  virtual ~GetFootprintContext() = default;

  // Returns the object-based view of the world associated with the skill.
  virtual absl::StatusOr<world::ObjectWorldClient> GetObjectWorld() = 0;

  // Returns the world object that represents the equipment in the world as
  // required by the skill within this context.
  virtual absl::StatusOr<world::KinematicObject> GetKinematicObjectForEquipment(
      absl::string_view equipment_name) = 0;
  virtual absl::StatusOr<world::WorldObject> GetObjectForEquipment(
      absl::string_view equipment_name) = 0;
  virtual absl::StatusOr<world::Frame> GetFrameForEquipment(
      absl::string_view equipment_name, absl::string_view frame_name) = 0;
};

// Interface definition of Skill projecting.
class SkillProjectInterface {
 public:
  using GetFootprintResult = intrinsic_proto::skills::GetFootprintResult;

  // Computes the skill's footprint. `world` contains the world under which the
  // skill is expected to operate, and this function should not modify it.
  virtual absl::StatusOr<GetFootprintResult> GetFootprint(
      const GetFootprintRequest& request, GetFootprintContext& context) const {
    GetFootprintResult result;
    result.mutable_footprint()->set_lock_the_universe(true);
    return std::move(result);
  }

  virtual ~SkillProjectInterface() = default;
};

// A request for a call to SkillInterface::Execute.
class ExecuteRequest {
 public:
  // `param_defaults` can specify default parameter values to merge into any
  // unset fields of `params`.
  ExecuteRequest(const ::google::protobuf::Message& params,
                 ::google::protobuf::Message* param_defaults = nullptr) {
    params_any_.PackFrom(params);
    if (param_defaults != nullptr) {
      param_defaults_any_ = google::protobuf::Any();
      param_defaults_any_->PackFrom(*param_defaults);
    }
  }

  // Defers conversion of input Any params to target proto type until accessed
  // by the user in params().
  //
  // This constructor enables conversion from Any to the target type without
  // needing a message pool/factory up front, since params() is templated on the
  // target type.
  ExecuteRequest(google::protobuf::Any params,
                 std::optional<::google::protobuf::Any> param_defaults)
      :  //
        params_any_(std::move(params)),
        param_defaults_any_(std::move(param_defaults)) {}

  // The skill parameters proto.
  template <class TParams>
  absl::StatusOr<TParams> params() const {
    return internal::ResolveParams<TParams>(params_any_, param_defaults_any_);
  }

 private:
  ::google::protobuf::Any params_any_;
  std::optional<::google::protobuf::Any> param_defaults_any_;
};

// Contains additional metadata and functionality for a skill execution that is
// provided by the skill service server to a skill. Allows, e.g., to modify the
// world or to invoke subskills.
//
// ExecutionContext helps support cooperative skill cancellation via a
// SkillCanceller. When a cancellation request is received, the skill should:
// 1) stop as soon as possible and leave resources in a safe and recoverable
//    state;
// 2) return absl::CancelledError.
class ExecuteContext {
 public:
  // Returns a SkillCanceller that supports cooperative cancellation of the
  // skill.
  virtual SkillCanceller& GetCanceller() = 0;

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
      const ExecuteRequest& request, ExecuteContext& context) {
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

namespace internal {

template <class TMsg>
absl::StatusOr<TMsg> UnpackParams(const ::google::protobuf::Any& msg_any,
                                  absl::string_view name) {
  if (msg_any.type_url().empty()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Cannot unpack empty Any %s to %s", name, TMsg::descriptor()->name()));
  }
  if (!msg_any.Is<TMsg>()) {
    return absl::InvalidArgumentError(
        absl::StrFormat("Cannot unpack Any %s of type %s to %s.", name,
                        msg_any.type_url(), TMsg::descriptor()->name()));
  }

  TMsg msg;
  if (!msg_any.UnpackTo(&msg)) {
    return absl::InternalError(
        absl::StrFormat("Failed to unpack Any %s of type %s to %s.", name,
                        msg_any.type_url(), TMsg::descriptor()->name()));
  }

  return msg;
}

template <class TMsg>
absl::StatusOr<TMsg> ResolveParams(
    const ::google::protobuf::Any& params_any,
    const std::optional<::google::protobuf::Any>& defaults_any) {
  INTRINSIC_ASSIGN_OR_RETURN(TMsg params,
                             UnpackParams<TMsg>(params_any, "params"));
  if (defaults_any.has_value()) {
    INTRINSIC_ASSIGN_OR_RETURN(TMsg defaults,
                               UnpackParams<TMsg>(*defaults_any, "defaults"));
    INTRINSIC_RETURN_IF_ERROR(MergeUnset(defaults, params));
  }

  return params;
}

}  // namespace internal
}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_
