// Copyright 2023 Intrinsic Innovation LLC

#include <cstring>

#include "absl/flags/parse.h"
#include "absl/flags/usage.h"
#include "absl/log/globals.h"
#include "absl/log/initialize.h"
#include "intrinsic/icon/utils/log.h"

void InitXfa(const char* usage, int argc, char* argv[]) {
  if (usage != nullptr && strlen(usage) > 0) {
    absl::SetProgramUsageMessage(usage);
  }
  absl::ParseCommandLine(argc, argv);
  absl::InitializeLog();
  absl::SetStderrThreshold(absl::LogSeverityAtLeast::kInfo);
  intrinsic::RtLogInitForThisThread();
}
