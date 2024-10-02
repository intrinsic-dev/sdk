// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/release/portable/init_xfa.h"

#include <cstdint>
#include <cstdlib>

#include "absl/base/log_severity.h"
#include "absl/flags/flag.h"
#include "absl/log/globals.h"
#include "absl/strings/string_view.h"

ABSL_FLAG(int64_t, int_flag, 0, "integer value for testing");

// Note: We can't use gtest as it's incompatible with the log init in InitXfa().
int main() {
  // Check the command line flags are parsed properly.
  int argc = 2;
  const char* argv[] = {"init_xfa_test", "--int_flag=10"};
  InitXfa(nullptr, argc, const_cast<char**>(argv));
  if (absl::GetFlag(FLAGS_int_flag) != 10) {
    return EXIT_FAILURE;
  }
  // Check that LOG(INFO) statements are sent to stderr.
  if (absl::StderrThreshold() != absl::LogSeverityAtLeast::kInfo) {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
