// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/util/thread/thread.h"

#include <sys/types.h>

#include <memory>

#include "absl/log/log.h"

#if defined(__linux__)
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#endif

#include <array>
#include <cstring>
#include <functional>
#include <optional>
#include <string>
#include <thread>  // NOLINT(build/c++11)
#include <utility>
#include <vector>

#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_guard.h"

namespace intrinsic {

namespace {

absl::string_view ShortName(absl::string_view name) {
  return name.length() < Thread::GetMaxNameLength()
             ? name
             : name.substr(name.length() - Thread::GetMaxNameLength() + 1,
                           Thread::GetMaxNameLength() - 1);
}

}  // namespace

// The settings are platform-dependent on Linux.
#if defined(__linux__)
Thread::Options& Thread::Options::SetRealtimeHighPriorityAndScheduler() {
  priority_ = 92;  // High real-time priority.
  policy_ = SCHED_FIFO;
  return *this;
}

Thread::Options& Thread::Options::SetRealtimeLowPriorityAndScheduler() {
  priority_ = 83;  // Low real-time priority.
  policy_ = SCHED_FIFO;
  return *this;
}

Thread::Options& Thread::Options::SetNormalPriorityAndScheduler() {
  priority_ = 0;
  policy_ = SCHED_OTHER;
  return *this;
}
#endif

Thread::Options& Thread::Options::SetPriority(int priority) {
  priority_ = priority;
  return *this;
}

Thread::Options& Thread::Options::SetSchedulePolicy(int policy) {
  policy_ = policy;
  return *this;
}

Thread::Options& Thread::Options::SetAffinity(const std::vector<int>& cpus) {
  cpus_ = cpus;
  return *this;
}

Thread::Options& Thread::Options::SetName(absl::string_view name) {
  name_ = std::string(name);
  return *this;
}

Thread::Thread() = default;

Thread::~Thread() {
  if (Joinable()) {
    char thread_name[kMaxNameLen];
    pthread_getname_np(thread_impl_.native_handle(), thread_name, kMaxNameLen);
    LOG(FATAL)
        << "The joinable thread '" << thread_name
        << "' is about to be destructed, but has not been joined! This will "
           "cause a termination by the C++ runtime. Adjust your thread logic.";
  }
}

void Thread::Join() {
  INTRINSIC_ASSERT_NON_REALTIME();
  thread_impl_.join();
}

bool Thread::Joinable() const { return thread_impl_.joinable(); }

absl::Status Thread::SetupAndStart(const Options& options,
                                   const std::function<void()>& f) {
  INTRINSIC_ASSERT_NON_REALTIME();

  if (thread_impl_.joinable()) {
    return absl::FailedPreconditionError("Thread can only be Start()ed once.");
  }

  std::shared_ptr<ThreadSetup> thread_setup = std::make_shared<ThreadSetup>();
  thread_impl_ = std::thread(&Thread::ThreadBody, f, options, thread_setup);

  const absl::Status setup_status = Setup(options);
  {
    // Communicate that we're no longer initializing.
    absl::MutexLock lock(&thread_setup->mutex);
    thread_setup->state = setup_status.ok() ? ThreadSetup::State::kSucceeded
                                            : ThreadSetup::State::kFailed;
  }
  if (!setup_status.ok()) {
    Join();
    return setup_status;
  }
  return absl::OkStatus();
}

absl::Status Thread::Setup(const Options& options) {
  INTRINSIC_ASSERT_NON_REALTIME();
  // A Thread constructed with the Thread(Function&& f, Args&&... args)
  // constructor should behave the same as a Thread constructed with Start() and
  // default constructed Options. To achieve this, we use optional parameters in
  // Options, and perform no setup work for each option that is unset. This is
  // checked within each Set*() method.
  INTRINSIC_RETURN_IF_ERROR(SetName(options));
  INTRINSIC_RETURN_IF_ERROR(SetSchedule(options));
  INTRINSIC_RETURN_IF_ERROR(SetAffinity(options));

  return absl::OkStatus();
}

absl::Status Thread::SetSchedule(const Options& options) {
#if !defined(_POSIX_THREAD_PRIORITY_SCHEDULING)
  return absl::UnimplementedError(
      "Schedule parameters are not currently supported for this platform.");
#else
  // If these are unset, use the platform default.
  if (!options.GetSchedulePolicy().has_value() &&
      !options.GetPriority().has_value()) {
    return absl::OkStatus();
  }

  int policy = SCHED_OTHER;
  if (options.GetSchedulePolicy().has_value()) {
    policy = options.GetSchedulePolicy().value();
  }

  int priority = 0;
  if (options.GetPriority().has_value()) {
    priority = options.GetPriority().value();
  }

  sched_param sch;
  sch.sched_priority = priority;
  if (int errnum =
          pthread_setschedparam(thread_impl_.native_handle(), policy, &sch);
      errnum != 0) {
    constexpr char kFailed[] = "Failed to set thread scheduling parameters.";
    if (errnum == EPERM) {
      return absl::PermissionDeniedError(absl::StrCat(
          kFailed, " The caller does not have appropriate privileges."));
    }

    if (errnum == EINVAL) {
      return absl::InvalidArgumentError(
          absl::StrCat(kFailed, "Policy: ", policy,
                       " is not a recognized policy, or priority: ", priority,
                       " does not make sense for this policy."));
    }

    // This can only happen if `thread_impl_` is default constructed at this
    // time. Our implementation of `Thread` should ensure that this can't be the
    // case.
    return absl::InternalError(
        absl::StrCat(kFailed, " ", std::strerror(errnum)));
  }
  return absl::OkStatus();
#endif
}

absl::Status Thread::SetAffinity(const Options& options) {
// pthread_setaffinity_np() is a nonstandard GNU extension recommended over the
// use of sched_setaffinity() when using the POSIX threads API. See:
// https://linux.die.net/man/2/sched_setaffinity and
// https://linux.die.net/man/3/pthread_setaffinity_np
#if !defined(_GNU_SOURCE)
  return absl::UnimplementedError(
      "Schedule parameters are not currently supported for this platform.");
#else
  // If the specified CPU set is empty, use the platform default CPU set for
  // thread affinity.
  if (options.GetCpuSet().empty()) {
    return absl::OkStatus();
  }

  cpu_set_t cpu_set;
  CPU_ZERO(&cpu_set);
  for (int cpu : options.GetCpuSet()) {
    CPU_SET(cpu, &cpu_set);
  }

  if (int errnum = pthread_setaffinity_np(thread_impl_.native_handle(),
                                          sizeof(cpu_set_t), &cpu_set);
      errnum != 0) {
    constexpr char kFailed[] = "Failed to set CPU affinity.";
    if (errnum == EINVAL) {
      return absl::InvalidArgumentError(
          absl::StrCat(kFailed, " Invalid cpu set specified.",
                       absl::StrJoin(options.GetCpuSet(), ", ")));
    }

    // This can only happen if `thread_impl_` is default constructed at this
    // time, or if we passed bad memory to pthread_setaffinity_np(...). Our
    // implementation of `Thread` should ensure that this can't be the case.
    return absl::InternalError(
        absl::StrCat(kFailed, " ", std::strerror(errnum)));
  }
  return absl::OkStatus();
#endif
}

absl::Status Thread::SetName(const Options& options) {
  if (!options.GetName().has_value()) return absl::OkStatus();

  if (int errnum = pthread_setname_np(thread_impl_.native_handle(),
                                      ShortName(*options.GetName()).data());
      errnum != 0) {
    return absl::InternalError(absl::StrCat(
        "Failed to set thread name. errnum: ", std::strerror(errnum)));
  }

  return absl::OkStatus();
}

void Thread::ThreadBody(const std::function<void()>& f, const Options& options,
                        std::shared_ptr<const ThreadSetup> thread_setup) {
  // Don't do work that can fail here, since we can't return a status from
  // `thread_impl_`'s thread of execution.
  {
    absl::MutexLock lock(&thread_setup->mutex);
    thread_setup->mutex.Await(absl::Condition(
        +[](const ThreadSetup::State* state) {
          return *state != ThreadSetup::State::kInitializing;
        },
        &thread_setup->state));
    if (thread_setup->state == ThreadSetup::State::kFailed) {
      return;
    }
  }

  const std::string short_name(ShortName(options.GetName().value_or("")));

  RtLogInitForThisThread();

  f();
}

}  // namespace intrinsic
