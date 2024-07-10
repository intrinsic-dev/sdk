// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread_options.h"

#include <sched.h>

#include <string>
#include <vector>

#include "absl/strings/string_view.h"

namespace intrinsic {

// The settings are platform-dependent on Linux.
ThreadOptions& ThreadOptions::SetRealtimeHighPriorityAndScheduler() {
  priority_ = 92;  // High real-time priority.
  policy_ = SCHED_FIFO;
  return *this;
}

ThreadOptions& ThreadOptions::SetRealtimeLowPriorityAndScheduler() {
  priority_ = 83;  // Low real-time priority.
  policy_ = SCHED_FIFO;
  return *this;
}

ThreadOptions& ThreadOptions::SetNormalPriorityAndScheduler() {
  priority_ = 0;
  policy_ = SCHED_OTHER;
  return *this;
}

ThreadOptions& ThreadOptions::SetPriority(int priority) {
  priority_ = priority;
  return *this;
}

ThreadOptions& ThreadOptions::SetSchedulePolicy(int policy) {
  policy_ = policy;
  return *this;
}

ThreadOptions& ThreadOptions::SetAffinity(const std::vector<int>& cpus) {
  cpus_ = cpus;
  return *this;
}

ThreadOptions& ThreadOptions::SetName(absl::string_view name) {
  name_ = std::string(name);
  return *this;
}

}  // namespace intrinsic
