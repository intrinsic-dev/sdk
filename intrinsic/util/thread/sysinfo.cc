// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/sysinfo.h"

#include <ctime>

#include "absl/time/time.h"

namespace intrinsic {

absl::Duration ThreadCPUUsage() {
  struct timespec spec;
  if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &spec) != 0) {
    return absl::ZeroDuration();
  }
  return absl::DurationFromTimespec(spec);
}

}  // namespace intrinsic
