// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/internal/skill_proto_utils.h"

#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/log/log.h"
#include "absl/memory/memory.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/types/span.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/message.h"
#include "intrinsic/assets/proto/documentation.pb.h"
#include "intrinsic/assets/proto/id.pb.h"
#include "intrinsic/skills/proto/equipment.pb.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/proto/source_code_info_view.h"
#include "intrinsic/util/status/status_macros.h"
#include "re2/re2.h"

namespace intrinsic {
namespace skills {

namespace {

// This is the recommended regex for semver. It is copied from
// https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
constexpr LazyRE2 kSemverRegex = {
    R"reg(^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$)reg"};

}  // namespace

void StripSourceCodeInfo(
    google::protobuf::FileDescriptorSet& file_descriptor_set) {
  for (google::protobuf::FileDescriptorProto& file :
       *file_descriptor_set.mutable_file()) {
    file.clear_source_code_info();
  }
}

namespace {

struct MessageData {
  std::string message_full_name;
  const google::protobuf::FileDescriptorSet& file_descriptor_set;
};

// Add file descriptor set for a skill's parameter and clear source code info.
absl::Status AddParameterDescription(
    const MessageData& parameter_data,
    std::unique_ptr<google::protobuf::Message> default_value,
    intrinsic_proto::skills::Skill& skill_proto) {
  intrinsic_proto::skills::ParameterDescription& parameter_description =
      *skill_proto.mutable_parameter_description();

  parameter_description.set_parameter_message_full_name(
      parameter_data.message_full_name);

  if (default_value != nullptr) {
    parameter_description.mutable_default_value()->PackFrom(*default_value);
  }

  *parameter_description.mutable_parameter_descriptor_fileset() =
      parameter_data.file_descriptor_set;
  SourceCodeInfoView source_code_info;
  if (absl::Status status =
          source_code_info.InitStrict(parameter_data.file_descriptor_set);
      !status.ok()) {
    if (status.code() == absl::StatusCode::kInvalidArgument) {
      return status;
    }
    if (status.code() == absl::StatusCode::kNotFound) {
      LOG(INFO) << "parameter FileDescriptorSet missing source_code_info, "
                   "comment map will be empty.";
      return absl::OkStatus();
    }
  }

  INTR_ASSIGN_OR_RETURN(
      *parameter_description.mutable_parameter_field_comments(),
      source_code_info.GetNestedFieldCommentMap(
          parameter_data.message_full_name));
  StripSourceCodeInfo(
      *parameter_description.mutable_parameter_descriptor_fileset());

  return absl::OkStatus();
}

// Add file descriptor set for a skill's return and clear source code info.
absl::Status AddReturnValueDescription(
    const MessageData& return_value_data,
    intrinsic_proto::skills::Skill& skill_proto) {
  intrinsic_proto::skills::ReturnValueDescription& return_value_description =
      *skill_proto.mutable_return_value_description();

  return_value_description.set_return_value_message_full_name(
      return_value_data.message_full_name);

  *return_value_description.mutable_descriptor_fileset() =
      return_value_data.file_descriptor_set;
  SourceCodeInfoView source_code_info;
  if (absl::Status status =
          source_code_info.InitStrict(return_value_data.file_descriptor_set);
      !status.ok()) {
    if (status.code() == absl::StatusCode::kInvalidArgument) {
      return status;
    }
    if (status.code() == absl::StatusCode::kNotFound) {
      LOG(INFO) << "return type FileDescriptorSet missing source_code_info, "
                   "comment map will be empty.";
      return absl::OkStatus();
    }
  }

  INTR_ASSIGN_OR_RETURN(
      *return_value_description.mutable_return_value_field_comments(),
      source_code_info.GetNestedFieldCommentMap(
          return_value_data.message_full_name));
  StripSourceCodeInfo(*return_value_description.mutable_descriptor_fileset());

  return absl::OkStatus();
}

absl::Status AddFileDescriptorSetWithoutSourceCodeInfo(
    std::unique_ptr<MessageData> parameter_data,
    std::unique_ptr<MessageData> return_value_data,
    std::unique_ptr<google::protobuf::Message> default_parameter_value,
    intrinsic_proto::skills::Skill& skill_proto) {
  if (parameter_data != nullptr) {
    INTR_RETURN_IF_ERROR(AddParameterDescription(
        *parameter_data, std::move(default_parameter_value), skill_proto));
  }

  if (return_value_data != nullptr) {
    INTR_RETURN_IF_ERROR(
        AddReturnValueDescription(*return_value_data, skill_proto));
  }

  return absl::OkStatus();
}

}  // namespace

absl::StatusOr<intrinsic_proto::skills::Skill> BuildSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& parameter_file_descriptor_set,
    const google::protobuf::FileDescriptorSet& return_value_file_descriptor_set,
    std::optional<absl::string_view> semver_version) {
  intrinsic_proto::skills::Skill skill;
  skill.set_skill_name(manifest.id().name());
  skill.set_id(manifest.id().package() + "." + manifest.id().name());
  skill.set_package_name(manifest.id().package());
  if (semver_version.has_value()) {
    if (!RE2::FullMatch(*semver_version, *kSemverRegex)) {
      return absl::InvalidArgumentError(
          absl::StrCat("semver_version: ", *semver_version,
                       " is not a valid semver version."));
    }
    skill.set_id_version(absl::StrCat(skill.id(), ".", *semver_version));
  } else {
    skill.set_id_version(skill.id());
  }
  skill.set_description(manifest.documentation().description());
  skill.set_display_name(manifest.display_name());
  *skill.mutable_resource_selectors() =
      manifest.dependencies().required_equipment();

  skill.mutable_execution_options()->set_supports_cancellation(
      manifest.options().supports_cancellation());

  INTR_RETURN_IF_ERROR(AddFileDescriptorSetWithoutSourceCodeInfo(
      manifest.has_parameter()
          ? absl::WrapUnique<MessageData>(new MessageData{
                .message_full_name = manifest.parameter().message_full_name(),
                .file_descriptor_set = parameter_file_descriptor_set,
            })
          : nullptr,
      manifest.has_return_type()
          ? absl::WrapUnique<MessageData>(new MessageData{
                .message_full_name = manifest.return_type().message_full_name(),
                .file_descriptor_set = return_value_file_descriptor_set,
            })
          : nullptr,
      nullptr, skill));

  if (manifest.has_parameter()) {
    if (manifest.parameter().has_default_value()) {
      *skill.mutable_parameter_description()->mutable_default_value() =
          manifest.parameter().default_value();
    }
  }
  return skill;
}

absl::StatusOr<intrinsic_proto::skills::Skill> BuildSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& file_descriptor_set,
    std::optional<absl::string_view> semver_version) {
  return BuildSkillProto(manifest, file_descriptor_set, file_descriptor_set,
                         semver_version);
}

}  // namespace skills
}  // namespace intrinsic
