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
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic {
namespace skills {

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
