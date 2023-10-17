// Copyright 2023 Intrinsic Innovation LLC

#include <cstdlib>
#include <string>

#include "absl/flags/flag.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/assets/proto/id.pb.h"
#include "intrinsic/icon/release/file_helpers.h"
#include "intrinsic/icon/release/portable/init_xfa.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"

ABSL_FLAG(std::string, manifest_pbbin_filename, "",
          "Path to the manifest binary proto file.");
ABSL_FLAG(std::string, output_pbbin_filename, "",
          "Path to file to write prototext id out to.");

namespace {

absl::Status GenSkillIdFile(absl::string_view manifest_pbbin_filename,
                            absl::string_view output_pbbin_filename) {
  INTRINSIC_ASSIGN_OR_RETURN(
      auto manifest,
      intrinsic::GetBinaryProto<intrinsic_proto::skills::Manifest>(
          manifest_pbbin_filename));

  LOG(INFO) << "writing: " << manifest.id() << " to: " << output_pbbin_filename;
  return intrinsic::SetBinaryProto(output_pbbin_filename, manifest.id());
}

}  // namespace

int main(int argc, char** argv) {
  InitXfa(argv[0], argc, argv);
  QCHECK_OK(GenSkillIdFile(absl::GetFlag(FLAGS_manifest_pbbin_filename),
                           absl::GetFlag(FLAGS_output_pbbin_filename)));
  return EXIT_SUCCESS;
}
