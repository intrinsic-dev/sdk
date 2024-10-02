// Copyright 2023 Intrinsic Innovation LLC

#include <string>

#include "absl/base/log_severity.h"
#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/globals.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "google/protobuf/descriptor.pb.h"
#include "google/protobuf/duration.pb.h"
#include "intrinsic/assets/proto/id.pb.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/skills/internal/skill_service_config_utils.h"
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
  const std::string manifest_pbbin_filename =
      absl::GetFlag(FLAGS_manifest_pbbin_filename);
  if (manifest_pbbin_filename.empty()) {
    return absl::InvalidArgumentError("A valid manifest is required.");
  }

  const std::string proto_descriptor_filename =
      absl::GetFlag(FLAGS_proto_descriptor_filename);
  if (proto_descriptor_filename.empty()) {
    return absl::InvalidArgumentError(
        "A valid proto_descriptor_filename is required.");
  }

  INTR_ASSIGN_OR_RETURN(
      intrinsic_proto::skills::SkillServiceConfig service_config,
      GetSkillServiceConfigFromManifest(manifest_pbbin_filename,
                                        proto_descriptor_filename));

  return SetBinaryProto(absl::GetFlag(FLAGS_output_config_filename),
                        service_config);
}

}  // namespace intrinsic::skills

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);
  // We change the stderr log threshold to minimize log spam in our build tools.
  absl::SetStderrThreshold(absl::LogSeverityAtLeast::kWarning);
  QCHECK_OK(intrinsic::skills::MainImpl());
  return 0;
}
