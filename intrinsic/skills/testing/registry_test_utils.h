// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_TESTING_REGISTRY_TEST_UTILS_H_
#define INTRINSIC_SKILLS_TESTING_REGISTRY_TEST_UTILS_H_

#include "absl/status/statusor.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic::skills {

// Gets a Skill proto that's ready for use in, for instance, the SkillRegistry
// config. Does not populate any default parameters. Specifies `kTestVersion` as
// the semver version.
absl::StatusOr<intrinsic_proto::skills::Skill> BuildTestSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& param_type_file_descriptor_set,
    const google::protobuf::FileDescriptorSet& return_type_file_descriptor_set);

}  // namespace intrinsic::skills

#endif  // INTRINSIC_SKILLS_TESTING_REGISTRY_TEST_UTILS_H_
