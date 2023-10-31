// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_
#define INTRINSIC_SKILLS_CC_SKILL_INTERFACE_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/message.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/footprint.pb.h"
#include "intrinsic/skills/proto/skill_service.pb.h"

// IWYU pragma: begin_exports
#include "intrinsic/skills/cc/execute_context.h"
#include "intrinsic/skills/cc/execute_request.h"
#include "intrinsic/skills/cc/get_footprint_context.h"
#include "intrinsic/skills/cc/get_footprint_request.h"
#include "intrinsic/skills/cc/preview_context.h"
#include "intrinsic/skills/cc/preview_request.h"
// IWYU pragma: end_exports

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
  // values are the `ResourceSelector`s corresponding to each 'slot'. The
  // `ResourceSelector`s describe the type of equipment required for the slot.
  virtual absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::ResourceSelector>
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

// Interface definition of Skill projecting.
class SkillProjectInterface {
 public:
  // Computes the skill's footprint. `world` contains the world under which the
  // skill is expected to operate, and this function should not modify it.
  virtual absl::StatusOr<intrinsic_proto::skills::Footprint> GetFootprint(
      const GetFootprintRequest& request, GetFootprintContext& context) const {
    intrinsic_proto::skills::Footprint result;
    result.set_lock_the_universe(true);
    return std::move(result);
  }

  virtual ~SkillProjectInterface() = default;
};

// Interface for Skill execution.
class SkillExecuteInterface {
 public:
  // Executes the skill. `context` provides access to the world and other
  // services that a skill may use.
  //
  // If skill execution succeeds, the skill should return either the skill's
  // result proto message, or nullptr if the skill has no output. If skill
  // execution fails, the skill should return an appropriate error status, as
  // described below.
  //
  // If the skill fails for one of the following reasons, it should return the
  // specified error along with a descriptive and, if possible, actionable error
  // message:
  // - `absl::CancelledError` if the skill is aborted due to a cancellation
  //   request (assuming the skill supports the cancellation).
  // - `absl::InvalidArgumentError` if the arguments provided as skill
  //   parameters are invalid.
  //
  // Refer to absl status documentation for other errors:
  // https://github.com/abseil/abseil-cpp/blob/master/absl/status/status.h
  //
  // Any error status returned by the skill will be handled by the executive
  // that runs the process to which the skill belongs. The effect of the error
  // will depend on how the skill is integrated into that process' behavior
  // tree. For instance, if the skill is part of a fallback node, a skill error
  // will trigger the fallback behavior. If the skill is not part of any node
  // that handles errors, then a skill error will cause the process to fail.
  //
  // Currently, there is no way to distinguish between potentially recoverable
  // failures that should lead to fallback handling (e.g., failure to achieve
  // the skill's objective) and other failures that should cause the entire
  // process to abort (e.g., failure to connect to a gRPC service).
  virtual absl::StatusOr<std::unique_ptr<google::protobuf::Message>> Execute(
      const ExecuteRequest& request, ExecuteContext& context) {
    return absl::UnimplementedError("Skill does not implement `Execute`.");
  }

  // Previews the expected outcome of executing the skill.
  //
  // Preview() enables an application developer to perform a "dry run" of skill
  // execution (or execution of a process that includes that skill) in order to
  // preview the effect of executing the skill/process, but without any
  // real-world side-effects that normal execution would entail.
  //
  // Skill developers should override this method with their implementation. The
  // implementation will not have access to hardware resources that are provided
  // to Execute(), but will have access to a hypothetical world in which to
  // preview the execution. The implementation should return the expected output
  // of executing the skill in that world.
  //
  // NOTE: In preview mode, the object world provided by the PreviewContext
  // is treated as the -actual- state of the physical world, rather than as the
  // belief state that it represents during normal skill execution. Because of
  // this difference, a skill in preview mode cannot introduce or correct
  // discrepancies between the physical and belief world (since they are
  // identical). For example, if a perception skill only updates the belief
  // state when it is executed, then its implementation of Preview() would
  // necessarily be a no-op.
  //
  // If executing the skill is expected to affect the physical world, then the
  // implementation should record the timing of its expected effects using
  // context.RecordWorldUpdate(). It should NOT make changes to the object
  // world via interaction with context.object_world().
  virtual absl::StatusOr<std::unique_ptr<::google::protobuf::Message>> Preview(
      const PreviewRequest& request, PreviewContext& context) {
    return absl::UnimplementedError("Skill does not implement `Preview`.");
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
