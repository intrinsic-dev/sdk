// Copyright 2023 Intrinsic Innovation LLC

#include <string>
#include <vector>

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

ABSL_FLAG(std::string, skill_name, "",
          "The name of the skill. The skill must be registered and linked in "
          "the build.");
ABSL_FLAG(std::string, manifest_pbbin_filename, "",
          "Filename for the prototext skill manifest.");
ABSL_FLAG(
    std::string, proto_descriptor_filename, "",
    "Filename for FileDescriptorSet for skill parameter, return value "
    "and published topic protos. If specified parameter_descriptor_filename, "
    "return_value_descriptor_filename, and pub_topic_descriptor_filename will "
    "be ignored");
ABSL_FLAG(std::string, parameter_descriptor_filename, "",
          "Filename for FileDescriptorSet for the skill parameters.");
ABSL_FLAG(
    std::string, return_value_descriptor_filename, "",
    "Optional filename for FileDescriptorSet for the skill return values.");
ABSL_FLAG(std::vector<std::string>, python_skill_modules, {},
          "List of skill modules that must be imported for a python skill.");
ABSL_FLAG(std::string, output_config_filename, "", "Output filename.");

namespace intrinsic::skills {

absl::Status MainImpl() {
  ::intrinsic_proto::skills::SkillServiceConfig service_config;

  // N.B. Pre-manifest we load the file descriptor sets at runtime of the skill
  // service, so the paths here should map to the path on the container image.
  service_config.set_parameter_descriptor_filename(
      absl::GetFlag(FLAGS_parameter_descriptor_filename));
  service_config.set_return_value_descriptor_filename(
      absl::GetFlag(FLAGS_return_value_descriptor_filename));

  // When using the manifest, we will also just load the data here because we
  // no longer need to run cpp or python skill in conjuntion with the file
  // descriptor sets to generate the skill config. This should simplify the
  // system design once we can delete the non-manifest path.
  if (std::string manifest_pbbin_filename =
          absl::GetFlag(FLAGS_manifest_pbbin_filename);
      !manifest_pbbin_filename.empty()) {
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

    std::string proto_descriptor_filename =
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
  } else {
    service_config.set_skill_name(absl::GetFlag(FLAGS_skill_name));
    if (std::vector<std::string> python_modules =
            absl::GetFlag(FLAGS_python_skill_modules);
        !python_modules.empty()) {
      service_config.mutable_python_config()->mutable_module_names()->Add(
          python_modules.begin(), python_modules.end());
    }
  }

  return SetBinaryProto(absl::GetFlag(FLAGS_output_config_filename),
                        service_config);
}

}  // namespace intrinsic::skills

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);
  QCHECK_OK(intrinsic::skills::MainImpl());
  return 0;
}
