// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_H_
#define INTRINSIC_UTIL_THREAD_THREAD_H_

#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <thread>  // NOLINT(build/c++11)
#include <utility>
#include <vector>

#include "absl/base/thread_annotations.h"
#include "absl/functional/bind_front.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/mutex.h"
#include "absl/types/optional.h"
#include "intrinsic/icon/utils/realtime_guard.h"

namespace intrinsic {

// The Thread class represents a single thread of execution. Threads allow
// multiple functions to execute concurrently.
class Thread {
 public:
  // Options for the thread. These allow for non-default behavior of the thread.
  class Options {
   public:
    Options() = default;
    Options(const Options&) = default;

    // Sets the name for the thread. The ability to set a kernel thread name is
    // platform-specific. The name's prefix will be truncated if it exceeds
    // Thread::GetMaxNameLength(). If unset, the thread will have a
    // platform-default name.
    Options& SetName(absl::string_view name);

    // Sets real-time high priority and real-time schedule policy for this
    // thread. If you need real-time, also consider setting `SetAffinity`.
    Options& SetRealtimeHighPriorityAndScheduler();

    // Sets real-time low priority and real-time schedule policy for this
    // thread. If you need real-time, also consider setting `SetAffinity`.
    // Threads with "RealtimeHighPriority" will preempt this thread.
    Options& SetRealtimeLowPriorityAndScheduler();

    // Sets normal, non-real-time priority and schedule policy for this thread.
    // This is necessary when the parent thread has different settings, i.e.
    // when you create a normal-priority thread from a real-time thread.
    // If the parent thread uses cpu affinity, you often do not want to inherit
    // that, so also consider setting different `SetAffinity`.
    Options& SetNormalPriorityAndScheduler();

    // Sets the cpu affinity for the thread. The available cpus depend on the
    // hardware.
    Options& SetAffinity(const std::vector<int>& cpus);

    // Sets the priority for the thread. The available priority range is
    // platform-specific.
    // Prefer SetRealtime*/SetNormal* to avoid platform-dependent arguments in
    // your code. In Linux, thread priority only has an effect when using
    // real-time scheduling
    // (https://man7.org/linux/man-pages/man7/sched.7.html).
    Options& SetPriority(int priority);

    // Sets the policy for the thread. The available policies are
    // platform-specific.
    // Prefer SetRealtime*/SetNormal* to avoid platform-dependent arguments in
    // your code.
    Options& SetSchedulePolicy(int policy);

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

  // Default constructs a Thread object, no new thread of execution is created
  // at this time.
  Thread();

  // Starts a thread of execution and executes the function `f` in the created
  // thread of execution with the arguments `args...`. The function 'f' and the
  // provided `args...` must be bind-able to a std::function<void()>. The thread
  // is constructed without setting any threading options, using the default
  // thread creation for the platform. This is equivalent to Start()ing a
  // default-constructed Thread with default `options`.
  template <typename Function, typename... Args>
  explicit Thread(Function&& f, Args&&... args);

  // Movable.
  //
  // std::terminate() will be called if `this->Joinable()` returns true.
  Thread(Thread&&) = default;
  Thread& operator=(Thread&&) = default;

  ~Thread();

  // Not copyable
  Thread(const Thread&) = delete;
  Thread& operator=(const Thread&) = delete;

  // Returns the maximum length of the name (including null terminator).
  static constexpr int GetMaxNameLength() { return kMaxNameLen; }

  // Starts a thread of execution with the specified `options`. The function `f`
  // is run in the created thread of execution with the arguments `args...`. The
  // function 'f' and the provided `args...` must be bind-able to a
  // std::function<void()>.
  template <typename Function, typename... Args>
  absl::Status Start(const Options& options, Function&& f, Args&&... args);

  // Blocks the current thread until `this` Thread finishes its execution.
  void Join();

  // Returns `true` if `this` is an active thread of execution. Note that a
  // default constructed `Thread` that has not been Start()ed successfully is
  // not Joinable(). A `Thread` that is finished executing code, but has not yet
  // been Join()ed is still considered an active thread of execution.
  bool Joinable() const;

 private:
  struct ThreadSetup {
    enum class State { kInitializing, kFailed, kSucceeded };
    mutable absl::Mutex mutex;
    State state ABSL_GUARDED_BY(mutex) = State::kInitializing;
  };

  // maximum length that can be used for a posix thread name.
  static constexpr int kMaxNameLen = 16;

  // Sets up the `thread_impl_` with the provided `options`, then runs the
  // function `f` in the new thread of execution if setup is successful. If
  // setup is unsuccessful, returns the setup errors on the calling thread.
  absl::Status SetupAndStart(const Options& options,
                             const std::function<void()>& f);

  // The following methods setup the `thread_impl_` based on the provided
  // `options`. If default Options are provided, these method are guaranteed to
  // return an OK-Status.
  absl::Status Setup(const Options& options);
  absl::Status SetSchedule(const Options& options);
  absl::Status SetAffinity(const Options& options);
  absl::Status SetName(const Options& options);

  // Runs in the new thread of execution `thread_impl_`. Waits until thread
  // setup is done, then either proceeds to run the user provided function `f`,
  // or in case of setup failure, join the `thread_impl_` and finish executing
  // the thread without running `f`.
  static void ThreadBody(const std::function<void()>& f, const Options& options,
                         std::shared_ptr<const ThreadSetup> thread_setup);

  std::thread thread_impl_;  // The new thread of execution
};

template <typename Function, typename... Args>
absl::Status Thread::Start(const Options& options, Function&& f,
                           Args&&... args) {
  return SetupAndStart(options, absl::bind_front(std::forward<Function>(f),
                                                 std::forward<Args>(args)...));
}

template <typename Function, typename... Args>
Thread::Thread(Function&& f, Args&&... args)
    : thread_impl_(absl::bind_front(std::forward<Function>(f),
                                    std::forward<Args>(args)...)) {
  INTRINSIC_ASSERT_NON_REALTIME();
}

inline bool operator==(const Thread::Options& lhs, const Thread::Options& rhs) {
  return lhs.GetPriority() == rhs.GetPriority() &&
         lhs.GetSchedulePolicy() == rhs.GetSchedulePolicy() &&
         lhs.GetCpuSet() == rhs.GetCpuSet();
}

inline bool operator!=(const Thread::Options& lhs, const Thread::Options& rhs) {
  return !(lhs == rhs);
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_H_
