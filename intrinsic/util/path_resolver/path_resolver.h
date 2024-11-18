// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_PATH_RESOLVER_PATH_RESOLVER_H_
#define INTRINSIC_UTIL_PATH_RESOLVER_PATH_RESOLVER_H_

#include <string>

#include "absl/strings/string_view.h"

namespace intrinsic {

/**
 * Generic resolver that will attempt to resolve runfiles or external
 * directories if available.
 */
class PathResolver {
 public:
  static std::string ResolveRunfilesDir();
  static std::string ResolveRunfilesPath(absl::string_view path);
  static std::string ResolveRunfilesPathForTest(absl::string_view path);
  static std::string ResolveRunfilesPathIfRelative(absl::string_view path);
};

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PATH_RESOLVER_PATH_RESOLVER_H_
