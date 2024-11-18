// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/path_resolver/path_resolver.h"

#include <string>

#include "absl/strings/match.h"
#include "absl/strings/string_view.h"
#include "ortools/base/path.h"
#include "tools/cpp/runfiles/runfiles.h"

namespace intrinsic {

using bazel::tools::cpp::runfiles::Runfiles;

std::string PathResolver::ResolveRunfilesDir() {
  return Runfiles::Create("")->Rlocation("ai_intrinsic_sdks");
}

std::string PathResolver::ResolveRunfilesPath(absl::string_view path) {
  return file::JoinPath(ResolveRunfilesDir(), path);
}

std::string PathResolver::ResolveRunfilesPathForTest(absl::string_view path) {
  std::string error;
  auto runfiles = Runfiles::CreateForTest(BAZEL_CURRENT_REPOSITORY, &error);
  std::string runfiles_dir = runfiles->Rlocation(BAZEL_CURRENT_REPOSITORY);
  return file::JoinPath(runfiles_dir, path);
}

std::string PathResolver::ResolveRunfilesPathIfRelative(
    absl::string_view path) {
  if (absl::StartsWith(path, "/")) return std::string(path);
  return ResolveRunfilesPath(path);
}

}  // namespace intrinsic
