// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread_utils.h"

#include <cerrno>
#include <cstring>
#include <memory>
#include <string>
#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "absl/base/thread_annotations.h"
#include "absl/functional/any_invocable.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_join.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/icon/utils/realtime_stack_trace.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic {

namespace {

struct ThreadSetup {
  enum class State { kInitializing, kFailed, kSucceeded };
  mutable absl::Mutex mutex;
  State state ABSL_GUARDED_BY(mutex) = State::kInitializing;
};

// A helper thread body which takes care that `f` is only executed when the
// thread is fully set up. In case of setup failure, the function `f` is not
// executed and the body returns immediately.
void ThreadBody(absl::AnyInvocable<void()> f, const ThreadOptions& options,
                std::unique_ptr<const ThreadSetup> thread_setup) {
  // Don't do work that can fail here, since we can't return a status from
  // a thread of execution.
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
  icon::InitRtStackTrace();

  f();
}

}  // namespace

absl::string_view ShortName(absl::string_view name) {
  return name.length() < GetMaxPosixThreadNameLength()
             ? name
             : name.substr(name.length() - GetMaxPosixThreadNameLength() + 1,
                           GetMaxPosixThreadNameLength() - 1);
}

absl::Status SetSchedule(const ThreadOptions& options,
                         std::thread::native_handle_type thread_handle) {
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
  if (int errnum = pthread_setschedparam(thread_handle, policy, &sch);
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

absl::Status SetAffinity(const ThreadOptions& options,
                         std::thread::native_handle_type thread_handle) {
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

  if (int errnum =
          pthread_setaffinity_np(thread_handle, sizeof(cpu_set_t), &cpu_set);
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

absl::Status SetName(const ThreadOptions& options,
                     std::thread::native_handle_type thread_handle) {
  if (!options.GetName().has_value()) return absl::OkStatus();

  if (int errnum = pthread_setname_np(thread_handle,
                                      ShortName(*options.GetName()).data());
      errnum != 0) {
    return absl::InternalError(absl::StrCat(
        "Failed to set thread name. errnum: ", std::strerror(errnum)));
  }

  return absl::OkStatus();
}

absl::Status SetThreadOptions(const ThreadOptions& options,
                              std::thread::native_handle_type thread_handle) {
  INTRINSIC_ASSERT_NON_REALTIME();
  // A Thread constructed with the Thread(Function&& f, Args&&... args)
  // constructor should behave the same as a Thread constructed with Start() and
  // default constructed Options. To achieve this, we use optional parameters in
  // Options, and perform no setup work for each option that is unset. This is
  // checked within each Set*() method.
  INTR_RETURN_IF_ERROR(SetName(options, thread_handle));
  INTR_RETURN_IF_ERROR(SetSchedule(options, thread_handle));
  INTR_RETURN_IF_ERROR(SetAffinity(options, thread_handle));

  return absl::OkStatus();
}

absl::StatusOr<std::thread> CreateThreadFromInvocable(
    const ThreadOptions& options, absl::AnyInvocable<void()> f) {
  INTRINSIC_ASSERT_NON_REALTIME();

  auto thread_setup = std::make_unique<ThreadSetup>();
  auto thread_setup_ptr = thread_setup.get();
  std::thread thread(ThreadBody, std::move(f), options,
                     std::move(thread_setup));
  const absl::Status setup_status =
      SetThreadOptions(options, thread.native_handle());
  {
    // Communicate that we're no longer initializing.
    absl::MutexLock lock(&thread_setup_ptr->mutex);
    thread_setup_ptr->state = setup_status.ok() ? ThreadSetup::State::kSucceeded
                                                : ThreadSetup::State::kFailed;
  }
  if (!setup_status.ok()) {
    thread.join();
    return setup_status;
  }
  return thread;
}

}  // namespace intrinsic
