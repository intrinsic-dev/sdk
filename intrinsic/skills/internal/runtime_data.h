// Copyright 2023 Intrinsic Innovation LLC

// This file contains data types that are used by the skill service at runtime
// to provide our internal framework access to metadata about skills. Classes
// defined here should not be used in user-facing contexts.

#ifndef INTRINSIC_SKILLS_INTERNAL_RUNTIME_DATA_H_
#define INTRINSIC_SKILLS_INTERNAL_RUNTIME_DATA_H_

#include <optional>
#include <string>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "absl/types/span.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor_database.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"

namespace intrinsic::skills::internal {

// Contains data about parameters that is required by the skill service at
// runtime.
class ParameterData {
 public:
  ParameterData() = default;

  // Constructs ParameterData with the `descriptor` for the parameter. `this`
  // holds a reference to `descriptor` for the life of `this`.
  ParameterData(const google::protobuf::Descriptor& descriptor,
                const google::protobuf::Any& default_value);
  explicit ParameterData(const google::protobuf::Descriptor& descriptor);

  ParameterData(const ParameterData& other) = default;
  ParameterData& operator=(const ParameterData& other) = default;

  // Returns a pointer to the descriptor for this parameter. May be nullptr if
  // `this` is default constructed.
  const google::protobuf::Descriptor* GetDescriptor() const {
    return descriptor_;
  }

  const std::optional<google::protobuf::Any>& GetDefault() const {
    return default_;
  }

 private:
  const google::protobuf::Descriptor* descriptor_;
  std::optional<google::protobuf::Any> default_ = std::nullopt;
};

// Contains data about return types that is required by the skill service at
// runtime.
class ReturnTypeData {
 public:
  ReturnTypeData() = default;

  // Constructs ReturnTypeData with the `descriptor` for the return type. `this`
  // holds a pointer to `descriptor` for the life of `this`. `descriptor` may be
  // a nullptr if there is no return type.
  explicit ReturnTypeData(const google::protobuf::Descriptor* descriptor);

  ReturnTypeData(const ReturnTypeData& other) = default;
  ReturnTypeData& operator=(const ReturnTypeData& other) = default;

  // Returns a pointer to the proto descriptor for the return type.
  //
  // Returns nullptr if there is no return type.
  const google::protobuf::Descriptor* GetDescriptor() const {
    return descriptor_;
  }

 private:
  const google::protobuf::Descriptor* descriptor_;
};

// Contains data about execution options for a skill that are relevant to the
// skill services.
class ExecutionOptions {
 public:
  ExecutionOptions() = default;
  explicit ExecutionOptions(bool supports_cancellation);
  ExecutionOptions(bool supports_cancellation,
                   absl::Duration cancellation_ready_timeout);

  ExecutionOptions(const ExecutionOptions& other) = default;
  ExecutionOptions& operator=(const ExecutionOptions& other) = default;

  // Returns true if the skill supports cancellation during execution.
  bool SupportsCancellation() const { return supports_cancellation_; }

  absl::Duration GetCancellationReadyTimeout() const {
    return cancellation_ready_timeout_;
  }

 private:
  bool supports_cancellation_ = false;
  absl::Duration cancellation_ready_timeout_ = absl::Seconds(30);
};

// Contains data about resources for a skill that are relevant to the
// skill services.
class ResourceData {
 public:
  ResourceData() = default;
  explicit ResourceData(const absl::flat_hash_map<
                        std::string, intrinsic_proto::skills::ResourceSelector>&
                            resources_required);

  ResourceData(const ResourceData& other) = default;
  ResourceData& operator=(const ResourceData& other) = default;

  const absl::flat_hash_map<std::string,
                            intrinsic_proto::skills::ResourceSelector>&
  GetRequiredResources() const {
    return resources_required_;
  }

 private:
  absl::flat_hash_map<std::string, intrinsic_proto::skills::ResourceSelector>
      resources_required_ = {};
};

// Contains data about skills that is relevant to the skill services.
class SkillRuntimeData {
 public:
  SkillRuntimeData() = default;
  SkillRuntimeData(const ParameterData& parameter_data,
                   const ReturnTypeData& return_type_data,
                   const ExecutionOptions& execution_options,
                   const ResourceData& resource_data, absl::string_view id);

  SkillRuntimeData(const SkillRuntimeData& other) = default;
  SkillRuntimeData& operator=(const SkillRuntimeData& other) = default;

  const ParameterData& GetParameterData() const { return parameter_data_; }

  const ReturnTypeData& GetReturnTypeData() const { return return_type_data_; }

  const ExecutionOptions& GetExecutionOptions() const {
    return execution_options_;
  }

  const ResourceData& GetResourceData() const { return resource_data_; }

  absl::string_view GetId() const { return id_; }

 private:
  ParameterData parameter_data_;
  ReturnTypeData return_type_data_;
  ExecutionOptions execution_options_;
  ResourceData resource_data_;
  std::string id_;
};

// Constructs RuntimeData from the given skill proto, and the explicitly
// provided descriptors.
//
// Returns an error if the message name of the descriptor doesn't match the
// expected message names in the skill proto.
//
// This applies a default `cancellation_ready_timeout` of 30 seconds to the
// Execution options if no timeout is specified, in order to match the behavior
// of the skill signature.
absl::StatusOr<SkillRuntimeData> GetRuntimeDataFrom(
    const intrinsic_proto::skills::SkillServiceConfig& skill_service_config,
    const google::protobuf::Descriptor* parameter_descriptor,
    const google::protobuf::Descriptor* return_type_descriptor);

}  // namespace intrinsic::skills::internal

#endif  // INTRINSIC_SKILLS_INTERNAL_RUNTIME_DATA_H_
