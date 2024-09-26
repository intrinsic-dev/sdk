// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_SYSINFO_H_
#define INTRINSIC_UTIL_THREAD_SYSINFO_H_

#include <sys/syscall.h>
#include <unistd.h>

#include <thread>  // NOLINT

#include "absl/time/time.h"

namespace intrinsic {

// Number of logical processors.
inline int NumCPUs() { return std::thread::hardware_concurrency(); }

// Return the total cpu time used by the current thread.
absl::Duration ThreadCPUUsage();

// Return the thread id of the current thread, as told by the system.
inline pid_t GetTID() { return static_cast<pid_t>(syscall(SYS_gettid)); }

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_SYSINFO_H_
