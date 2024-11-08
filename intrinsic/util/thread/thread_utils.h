// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_
#define INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_

#include <thread>  // NOLINT(build/c++11)

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/util/thread/thread_options.h"

namespace intrinsic {

constexpr int GetMaxPosixThreadNameLength() {
  // maximum length that can be used for a posix thread name.
  constexpr int kMaxNameLen = 16;
  return kMaxNameLen;
}

absl::string_view ShortName(absl::string_view name);

absl::Status SetSchedule(const ThreadOptions& options,
                         std::thread::native_handle_type thread_handle);

absl::Status SetAffinity(const ThreadOptions& options,
                         std::thread::native_handle_type thread_handle);

absl::Status SetName(const ThreadOptions& options,
                     std::thread::native_handle_type thread_handle);

// Sets the name of the thread if possible and logs a warning otherwise.
// For intrinsic::Thread, the native handle can be obtained via
// Thread::NativeHandle().
absl::Status SetThreadName(absl::string_view name,
                           std::thread::native_handle_type thread_handle);

// For intrinsic::Thread, the native handle can be obtained via
// Thread::NativeHandle().
absl::Status SetThreadOptions(const ThreadOptions& options,
                              std::thread::native_handle_type thread_handle);

// Creates a thread and sets it up with the provided `options`, then runs the
// function `f` in the new thread of execution if setup is successful. If
// setup is unsuccessful, returns the setup errors on the calling thread.
absl::StatusOr<std::thread> CreateThreadFromInvocable(
    const ThreadOptions& options, absl::AnyInvocable<void()> f);

template <typename Function, typename... Args>
absl::StatusOr<std::thread> CreateThread(const ThreadOptions& options,
                                         Function&& f, Args&&... args) {
  return CreateThreadFromInvocable(
      options,
      std::bind_front(std::forward<Function>(f), std::forward<Args>(args)...));
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_
