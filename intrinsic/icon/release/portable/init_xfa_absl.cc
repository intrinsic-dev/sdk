// Copyright 2023 Intrinsic Innovation LLC

#include <cstring>

#include "absl/flags/flag.h"
#include "absl/flags/parse.h"
#include "absl/flags/usage.h"
#include "absl/log/globals.h"
#include "absl/log/initialize.h"
#include "absl/log/log.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/utils/log.h"

ABSL_FLAG(bool, sleep, false,
          "(optional) Do nothing and sleep indefinitely. This is used to "
          "download the image and avoid crash looping.");

void InitXfa(const char* usage, int argc, char* argv[]) {
  if (usage != nullptr && strlen(usage) > 0) {
    absl::SetProgramUsageMessage(usage);
  }
  absl::ParseCommandLine(argc, argv);
  absl::InitializeLog();
  absl::SetStderrThreshold(absl::LogSeverityAtLeast::kInfo);
  intrinsic::RtLogInitForThisThread();

  if (absl::GetFlag(FLAGS_sleep)) {
    LOG(INFO) << "Started with --sleep=true. Sleeping indefinitely...";
    absl::SleepFor(absl::InfiniteDuration());
  }

  LOG(INFO) << "********* Process Begin *********";
}
