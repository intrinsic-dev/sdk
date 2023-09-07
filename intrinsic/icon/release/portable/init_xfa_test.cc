// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/release/portable/init_xfa.h"

#include <gtest/gtest.h>

#include <cstdint>

#include "absl/flags/flag.h"
#include "absl/strings/string_view.h"

ABSL_FLAG(int64_t, int_flag, 0, "integer value for testing");

namespace {

TEST(InitXfaTest, ParseFlags) {
  int argc = 2;
  const char* argv[] = {"init_xfa_test", "--int_flag=10"};
  InitXfa(nullptr, argc, const_cast<char**>(argv));
  EXPECT_EQ(absl::GetFlag(FLAGS_int_flag), 10);
}

}  // namespace
