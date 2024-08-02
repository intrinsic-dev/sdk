// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_H_
#define INTRINSIC_UTIL_THREAD_THREAD_H_

#include <thread>  // NOLINT(build/c++11)
#include <type_traits>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/stop_token.h"
#include "intrinsic/util/thread/thread_options.h"
#include "intrinsic/util/thread/thread_utils.h"

namespace intrinsic {

// The Thread class represents a single thread of execution. Threads allow
// multiple functions to execute concurrently.
class Thread {
 public:
  // Default constructs a Thread object, no new thread of execution is created
  // at this time.
  Thread();

  // Starts a thread of execution and executes the function `f` in the created
  // thread of execution with the arguments `args...`. The function 'f' and the
  // provided `args...` must be bind-able to an absl::AnyInvocable<void()>. The
  // thread is constructed without setting any threading options, using the
  // default thread creation for the platform. This is equivalent to Start()ing
  // a default-constructed Thread with default `options`.
  // The 'requires' clause is to prevent the user from passing a Thread object
  // to the constructor (i.e. prevent confusion with the move ctor).
  template <typename Function, typename... Args>
  explicit Thread(Function&& f, Args&&... args)
    requires(!std::is_same_v<std::remove_cvref_t<Function>, Thread>)
      : stop_source_{StopSource{}},
        thread_impl_(InitThread(stop_source_, std::forward<Function>(f),
                                std::forward<Args>(args)...)) {
    INTRINSIC_ASSERT_NON_REALTIME();
    SaveStopToken();
  }

  // Movable.
  Thread(Thread&&);
  Thread& operator=(Thread&& other);

  // Destroys the Thread object.
  // If *this has an associated thread (Joinable() == true), calls RequestStop()
  // and then Join().
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
    INTRINSIC_ASSERT_NON_REALTIME();
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

  // Returns a StopSource associated with the same shared stop-state as held
  // internally by the Thread object.
  StopSource GetStopSource() noexcept;

  // Returns a StopToken associated with the same shared stop-state held
  // internally by the Thread object.
  StopToken GetStopToken() const noexcept;

  // Issues a stop request to the internal stop-state, if it has not yet already
  // had stop requested.
  bool RequestStop() noexcept;

 private:
  explicit Thread(std::thread&& thread) noexcept
      : stop_source_{StopSource{}}, thread_impl_(std::move(thread)) {
    SaveStopToken();
  }

  template <typename Function, typename... Args>
  static std::thread InitThread(const StopSource& ss, Function&& f,
                                Args&&... args) {
    if constexpr (std::is_invocable_v<std::decay_t<Function>, StopToken,
                                      std::decay_t<Args>...>) {
      // f takes a StopToken as its first argument, so pass it along.
      return std::thread(std::forward<Function>(f), ss.get_token(),
                         std::forward<Args>(args)...);
    } else {
      return std::thread(std::forward<Function>(f),
                         std::forward<Args>(args)...);
    }
  }

  void SaveStopToken() noexcept;

  // Explicit erase of the stop token. This is necessary to prevent a new thread
  // starting and a client calling ThisThreadStopRequested() before the
  // StopToken is associated with the thread.
  void EraseStopToken() noexcept;

  StopSource stop_source_{detail::NoState};
  std::thread thread_impl_;

  // We cannot rely on using the thread_impl_.get_id() because the thread may
  // have been finished or joined.
  std::thread::id thread_id_;
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

// Allows client code which is executed in a thread to call
//   while (!ThisThreadStopRequested()) {
//     // do something
//   }
// IMPORTANT: This function allocates a reader mutex in each call. Do not use it
// in hot loops. Instead, use a StopToken and check the stop_requested() state
// directly.
bool ThisThreadStopRequested();

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_H_
