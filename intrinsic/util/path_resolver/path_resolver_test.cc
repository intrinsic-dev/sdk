// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/path_resolver/path_resolver.h"

#include <gtest/gtest.h>

#include <string>
#include <string_view>

namespace intrinsic {
namespace {

TEST(PathResolver, Resolve) {
  std::string run_file = "intrinsic/util/path_resolver/path_resolver_test.cc";

  std::string full_path =
      PathResolver::ResolveRunfilesPath(std::string_view(run_file));
  EXPECT_NE(full_path.size(), 0);
  EXPECT_NE(full_path, run_file);
}

TEST(PathResolver, ResolveRunfilesPathIfRelative) {
  EXPECT_EQ(PathResolver::ResolveRunfilesPathIfRelative("/absolute/path"),
            "/absolute/path");
  EXPECT_EQ(PathResolver::ResolveRunfilesPathIfRelative("relative/path"),
            PathResolver::ResolveRunfilesPath("relative/path"));
}

}  // namespace
}  // namespace intrinsic
