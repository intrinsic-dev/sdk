// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_H_
#define INTRINSIC_UTIL_THREAD_THREAD_H_

#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "absl/functional/bind_front.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread_options.h"
#include "intrinsic/util/thread/thread_utils.h"

namespace intrinsic {

// The Thread class represents a single thread of execution. Threads allow
// multiple functions to execute concurrently.
class Thread {
 public:
  using Options = ThreadOptions;

  // Default constructs a Thread object, no new thread of execution is created
  // at this time.
  Thread();

  // Starts a thread of execution and executes the function `f` in the created
  // thread of execution with the arguments `args...`. The function 'f' and the
  // provided `args...` must be bind-able to an absl::AnyInvocable<void()>. The
  // thread is constructed without setting any threading options, using the
  // default thread creation for the platform. This is equivalent to Start()ing
  // a default-constructed Thread with default `options`.
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

  // Creates a new thread of execution with the specified `options`. The
  // function `f` is run in the created thread of execution with the arguments
  // `args...`. The function 'f' and the provided `args...` must be bind-able to
  // an absl::AnyInvocable<void()>.
  template <typename Function, typename... Args>
  absl::StatusOr<Thread> Create(const ThreadOptions& options, Function&& f,
                                Args&&... args) {
    INTR_ASSIGN_OR_RETURN(std::thread thread,
                          CreateThread(options, std::forward<Function>(f),
                                       std::forward<Args>(args)...));
    return Thread{std::move(thread)};
  }

  // Starts a thread of execution with the specified `options`. The function `f`
  // is run in the created thread of execution with the arguments `args...`. The
  // function 'f' and the provided `args...` must be bind-able to an
  // absl::AnyInvocable<void()>.
  template <typename Function, typename... Args>
  absl::Status Start(const ThreadOptions& options, Function&& f,
                     Args&&... args);

  // Blocks the current thread until `this` Thread finishes its execution.
  void Join();

  // Returns `true` if `this` is an active thread of execution. Note that a
  // default constructed `Thread` that has not been Start()ed successfully is
  // not Joinable(). A `Thread` that is finished executing code, but has not yet
  // been Join()ed is still considered an active thread of execution.
  bool Joinable() const;

 private:
  explicit Thread(std::thread&& thread) noexcept
      : thread_impl_(std::move(thread)) {}

  std::thread thread_impl_;  // The new thread of execution
};

template <typename Function, typename... Args>
absl::Status Thread::Start(const ThreadOptions& options, Function&& f,
                           Args&&... args) {
  INTRINSIC_ASSERT_NON_REALTIME();
  if (thread_impl_.joinable()) {
    return absl::FailedPreconditionError("Thread can only be Start()ed once.");
  }
  INTR_ASSIGN_OR_RETURN(*this,
                        Thread::Create(options, std::forward<Function>(f),
                                       std::forward<Args>(args)...));
  return absl::OkStatus();
}

template <typename Function, typename... Args>
Thread::Thread(Function&& f, Args&&... args)
    : thread_impl_(absl::bind_front(std::forward<Function>(f),
                                    std::forward<Args>(args)...)) {
  INTRINSIC_ASSERT_NON_REALTIME();
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_H_
