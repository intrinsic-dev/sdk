// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_SKILL_PROTO_UTILS_H_
#define INTRINSIC_SKILLS_INTERNAL_SKILL_PROTO_UTILS_H_

#include <optional>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/message.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic {
namespace skills {

// Gets a Skill proto that's ready for use in, for instance, the SkillRegistry
// config. Does not populate any default parameters. If semver_version is not
// specified will set id_version = id.
// Returns an error if `semver_version` is not valid semver.
absl::StatusOr<intrinsic_proto::skills::Skill> BuildSkillProto(
    const SkillSignatureInterface& skill_interface,
    std::optional<absl::string_view> semver_version = std::nullopt);

// Adds (or overwrites) the skill's parameter/return value descriptor fileset.
// This also populates the parameter and return value field comments. We remove
// source_code_info as it is no longer needed after the parameter and return
// value field comments are populated.
absl::Status AddFileDescriptorSetWithoutSourceCodeInfo(
    const SkillSignatureInterface& skill_interface,
    const google::protobuf::FileDescriptorSet& parameter_file_descriptor_set,
    const google::protobuf::FileDescriptorSet& return_value_file_descriptor_set,
    intrinsic_proto::skills::Skill& skill_proto);

absl::StatusOr<intrinsic_proto::skills::Skill> BuildSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& parameter_file_descriptor_set,
    const google::protobuf::FileDescriptorSet& return_value_file_descriptor_set,
    std::optional<absl::string_view> semver_version = std::nullopt);

// A convenience wrapper for the above when all file_descriptor_sets are the
// same.
absl::StatusOr<intrinsic_proto::skills::Skill> BuildSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& file_descriptor_set,
    std::optional<absl::string_view> semver_version = std::nullopt);

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_SKILL_PROTO_UTILS_H_
