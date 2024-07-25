// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/internal/runtime_data.h"

#include <iterator>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/algorithm/container.h"
#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "absl/types/span.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/descriptor_database.h"
#include "intrinsic/assets/proto/status_spec.pb.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::skills::internal {
namespace {}  // namespace

ParameterData::ParameterData(const google::protobuf::Any& default_value)
    : default_(default_value) {}

ExecutionOptions::ExecutionOptions(
    bool supports_cancellation,
    std::optional<absl::Duration> cancellation_ready_timeout,
    std::optional<absl::Duration> execution_timeout)
    : supports_cancellation_(supports_cancellation) {
  if (cancellation_ready_timeout.has_value()) {
    cancellation_ready_timeout_ = *cancellation_ready_timeout;
  }
  if (execution_timeout.has_value()) {
    execution_timeout_ = *execution_timeout;
  }
}

ResourceData::ResourceData(
    const absl::flat_hash_map<std::string,
                              intrinsic_proto::skills::ResourceSelector>&
        resources_required)
    : resources_required_(resources_required) {}

StatusSpecs::StatusSpecs(
    const std::vector<intrinsic_proto::assets::StatusSpec>& specs) {
  absl::c_transform(specs, std::inserter(specs_, specs_.end()),
                    [](const intrinsic_proto::assets::StatusSpec& spec) {
                      return std::make_pair(spec.code(), spec);
                    });
}

SkillRuntimeData::SkillRuntimeData(const ParameterData& parameter_data,
                                   const ReturnTypeData& return_type_data,
                                   const ExecutionOptions& execution_options,
                                   const ResourceData& resource_data,
                                   const StatusSpecs& status_specs,
                                   absl::string_view id)
    : parameter_data_(parameter_data),
      return_type_data_(return_type_data),
      execution_options_(execution_options),
      resource_data_(resource_data),
      status_specs_(status_specs),
      id_(id) {}

absl::StatusOr<SkillRuntimeData> GetRuntimeDataFrom(
    const intrinsic_proto::skills::SkillServiceConfig& skill_service_config) {
  std::optional<absl::Duration> cancellation_ready_timeout;
  if (skill_service_config.execution_service_options()
          .has_cancellation_ready_timeout()) {
    cancellation_ready_timeout =
        ToAbslDuration(skill_service_config.execution_service_options()
                           .cancellation_ready_timeout());
  }

  std::optional<absl::Duration> execution_timeout;
  if (skill_service_config.execution_service_options()
          .has_execution_timeout()) {
    execution_timeout = ToAbslDuration(
        skill_service_config.execution_service_options().execution_timeout());
  }

  return SkillRuntimeData(
      skill_service_config.skill_description()
              .parameter_description()
              .has_default_value()
          ? ParameterData(skill_service_config.skill_description()
                              .parameter_description()
                              .default_value())
          : ParameterData(),
      ReturnTypeData(),
      ExecutionOptions(skill_service_config.skill_description()
                           .execution_options()
                           .supports_cancellation(),
                       cancellation_ready_timeout, execution_timeout),
      ResourceData({skill_service_config.skill_description()
                        .resource_selectors()
                        .begin(),
                    skill_service_config.skill_description()
                        .resource_selectors()
                        .end()}),
      StatusSpecs({skill_service_config.status_info().begin(),
                   skill_service_config.status_info().end()}),
      skill_service_config.skill_description().id());
}

}  // namespace intrinsic::skills::internal
