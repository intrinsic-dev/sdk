// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_OPTIONS_H_
#define INTRINSIC_UTIL_THREAD_THREAD_OPTIONS_H_

#include <optional>
#include <string>
#include <vector>

#include "absl/strings/string_view.h"

namespace intrinsic {

// Options for the thread. These allow for non-default behavior of the thread.
class ThreadOptions {
 public:
  ThreadOptions() = default;

  // Sets the name for the thread. The ability to set a kernel thread name is
  // platform-specific. The name's prefix will be truncated if it exceeds
  // GetMaxPosixThreadNameLength(). If unset, the thread will have a
  // platform-default name.
  ThreadOptions& SetName(absl::string_view name);

  // Sets real-time high priority and real-time schedule policy for this
  // thread. If you need real-time, also consider setting `SetAffinity`.
  ThreadOptions& SetRealtimeHighPriorityAndScheduler();

  // Sets real-time low priority and real-time schedule policy for this
  // thread. If you need real-time, also consider setting `SetAffinity`.
  // Threads with "RealtimeHighPriority" will preempt this thread.
  ThreadOptions& SetRealtimeLowPriorityAndScheduler();

  // Sets normal, non-real-time priority and schedule policy for this thread.
  // This is necessary when the parent thread has different settings, i.e.
  // when you create a normal-priority thread from a real-time thread.
  // If the parent thread uses cpu affinity, you often do not want to inherit
  // that, so also consider setting different `SetAffinity`.
  ThreadOptions& SetNormalPriorityAndScheduler();

  // Sets the cpu affinity for the thread. The available cpus depend on the
  // hardware.
  ThreadOptions& SetAffinity(const std::vector<int>& cpus);

  // Sets the priority for the thread. The available priority range is
  // platform-specific.
  // Prefer SetRealtime*/SetNormal* to avoid platform-dependent arguments in
  // your code. In Linux, thread priority only has an effect when using
  // real-time scheduling
  // (https://man7.org/linux/man-pages/man7/sched.7.html).
  ThreadOptions& SetPriority(int priority);

  // Sets the policy for the thread. The available policies are
  // platform-specific.
  // Prefer SetRealtime*/SetNormal* to avoid platform-dependent arguments in
  // your code.
  ThreadOptions& SetSchedulePolicy(int policy);

  // Returns the priority, which may be unset.
  std::optional<int> GetPriority() const { return priority_; }

  // Returns the schedule policy, which may be unset.
  std::optional<int> GetSchedulePolicy() const { return policy_; }

  // Returns the thread name, which may be unset.
  std::optional<std::string> GetName() const { return name_; }

  // Returns an empty vector if the affinity is unset.
  const std::vector<int>& GetCpuSet() const { return cpus_; }

 private:
  std::optional<int> priority_;
  std::optional<int> policy_;
  std::optional<std::string> name_;
  // Not part of equals check.
  // Not part of equals check.

  // a zero-sized vector is considered to be unset, since it makes no sense to
  // specify that a thread runs on no cpus.
  std::vector<int> cpus_;
};

inline bool operator==(const ThreadOptions& lhs, const ThreadOptions& rhs) {
  return lhs.GetPriority() == rhs.GetPriority() &&
         lhs.GetSchedulePolicy() == rhs.GetSchedulePolicy() &&
         lhs.GetCpuSet() == rhs.GetCpuSet();
}

inline bool operator!=(const ThreadOptions& lhs, const ThreadOptions& rhs) {
  return !(lhs == rhs);
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_OPTIONS_H_
