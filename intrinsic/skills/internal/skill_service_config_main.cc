// Copyright 2023 Intrinsic Innovation LLC

#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/duration.pb.h"
#include "intrinsic/assets/proto/id.pb.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/skills/internal/skill_proto_utils.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/proto/skill_service_config.pb.h"
#include "intrinsic/skills/proto/skills.pb.h"
#include "intrinsic/util/status/status_macros.h"

ABSL_FLAG(std::string, manifest_pbbin_filename, "",
          "Filename for the binary skill manifest proto.");
ABSL_FLAG(std::string, proto_descriptor_filename, "",
          "Filename for FileDescriptorSet for skill parameter, return value "
          "and published topic protos.");
ABSL_FLAG(std::string, output_config_filename, "", "Output filename.");

namespace intrinsic::skills {

absl::Status MainImpl() {
  ::intrinsic_proto::skills::SkillServiceConfig service_config;

  const std::string manifest_pbbin_filename =
      absl::GetFlag(FLAGS_manifest_pbbin_filename);
  if (manifest_pbbin_filename.empty()) {
    return absl::InvalidArgumentError("A valid manifest is required.");
  }
  LOG(INFO) << "Loading Manifest from " << manifest_pbbin_filename;
  INTR_ASSIGN_OR_RETURN(
      auto manifest,
      intrinsic::GetBinaryProto<intrinsic_proto::skills::Manifest>(
          manifest_pbbin_filename));
  service_config.set_skill_name(manifest.id().name());

  if (manifest.options().has_cancellation_ready_timeout()) {
    *service_config.mutable_execution_service_options()
         ->mutable_cancellation_ready_timeout() =
        manifest.options().cancellation_ready_timeout();
  }

  const std::string proto_descriptor_filename =
      absl::GetFlag(FLAGS_proto_descriptor_filename);
  if (proto_descriptor_filename.empty()) {
    return absl::InvalidArgumentError(
        "A valid proto_descriptor_filename is required.");
  }
  LOG(INFO) << "Loading FileDescriptorSet from " << proto_descriptor_filename;
  INTR_ASSIGN_OR_RETURN(
      auto file_descriptor_set,
      intrinsic::GetBinaryProto<google::protobuf::FileDescriptorSet>(
          proto_descriptor_filename));

  INTR_ASSIGN_OR_RETURN(*service_config.mutable_skill_description(),
                        BuildSkillProto(manifest, file_descriptor_set));

  return SetBinaryProto(absl::GetFlag(FLAGS_output_config_filename),
                        service_config);
}

}  // namespace intrinsic::skills

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);
  QCHECK_OK(intrinsic::skills::MainImpl());
  return 0;
}
