// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/testing/registry_test_utils.h"

#include "absl/status/statusor.h"
#include "google/protobuf/descriptor.pb.h"
#include "intrinsic/assets/testing/id_test_utils.h"
#include "intrinsic/skills/internal/skill_proto_utils.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"

namespace intrinsic::skills {

absl::StatusOr<intrinsic_proto::skills::Skill> BuildTestSkillProto(
    const intrinsic_proto::skills::Manifest& manifest,
    const google::protobuf::FileDescriptorSet& param_type_file_descriptor_set,
    const google::protobuf::FileDescriptorSet&
        return_type_file_descriptor_set) {
  return skills::BuildSkillProto(manifest, param_type_file_descriptor_set,
                                 return_type_file_descriptor_set, kTestVersion);
}

}  // namespace intrinsic::skills
