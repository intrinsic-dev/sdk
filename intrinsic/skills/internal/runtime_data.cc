// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/internal/runtime_data.h"

#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "absl/types/span.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor_database.h"
#include "intrinsic/assets/id_utils.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::skills::internal {
namespace {}  // namespace

ParameterData::ParameterData(const google::protobuf::Descriptor& descriptor,
                             const google::protobuf::Any& default_value)
    : descriptor_(&descriptor), default_(default_value) {}

ParameterData::ParameterData(const google::protobuf::Descriptor& descriptor)
    : descriptor_(&descriptor), default_(std::nullopt) {}

ReturnTypeData::ReturnTypeData(const google::protobuf::Descriptor* descriptor)
    : descriptor_(descriptor) {}

ExecutionOptions::ExecutionOptions(bool supports_cancellation)
    : supports_cancellation_(supports_cancellation) {}

ExecutionOptions::ExecutionOptions(bool supports_cancellation,
                                   absl::Duration cancellation_ready_timeout)
    : supports_cancellation_(supports_cancellation),
      cancellation_ready_timeout_(cancellation_ready_timeout) {}

ResourceData::ResourceData(
    const absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::ResourceSelector>&
        resources_required)
    : resources_required_(resources_required) {}

SkillRuntimeData::SkillRuntimeData(const ParameterData& parameter_data,
                                   const ReturnTypeData& return_type_data,
                                   const ExecutionOptions& execution_options,
                                   const ResourceData& resource_data,
                                   absl::string_view id)
    : parameter_data_(parameter_data),
      return_type_data_(return_type_data),
      execution_options_(execution_options),
      resource_data_(resource_data),
      id_(id) {}

absl::StatusOr<SkillRuntimeData> GetRuntimeDataFrom(
    const intrinsic_proto::skills::SkillServiceConfig& skill_service_config,
    const google::protobuf::Descriptor* parameter_descriptor,
    const google::protobuf::Descriptor* return_type_descriptor) {
  return SkillRuntimeData(
      skill_service_config.skill_description()
              .parameter_description()
              .has_default_value()
          ? ParameterData(*parameter_descriptor,
                          skill_service_config.skill_description()
                              .parameter_description()
                              .default_value())
          : ParameterData(*parameter_descriptor),
      ReturnTypeData(return_type_descriptor),
      skill_service_config.execution_service_options()
              .has_cancellation_ready_timeout()
          ? ExecutionOptions(
                skill_service_config.skill_description()
                    .execution_options()
                    .supports_cancellation(),
                FromProto(skill_service_config.execution_service_options()
                              .cancellation_ready_timeout()))
          : ExecutionOptions(skill_service_config.skill_description()
                                 .execution_options()
                                 .supports_cancellation()),
      ResourceData({skill_service_config.skill_description()
                        .resource_selectors()
                        .begin(),
                    skill_service_config.skill_description()
                        .resource_selectors()
                        .end()}),
      skill_service_config.skill_description().id());
}

}  // namespace intrinsic::skills::internal
