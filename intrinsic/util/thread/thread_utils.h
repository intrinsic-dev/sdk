// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_
#define INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_

#include <functional>
#include <thread>  // NOLINT(build/c++11)
#include <tuple>
#include <type_traits>
#include <utility>

#include "absl/functional/any_invocable.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/util/thread/stop_token.h"
#include "intrinsic/util/thread/thread.h"
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
absl::StatusOr<Thread> CreateThreadFromInvocable(
    const ThreadOptions& options, absl::AnyInvocable<void(StopToken)> f);

template <typename Function, typename... Args>
absl::StatusOr<Thread> CreateThread(const ThreadOptions& options, Function&& f,
                                    Args&&... args) {
  // This is a compile time check if the first parameter of the function is a
  // StopToken.
  if constexpr (std::is_invocable_v<std::decay_t<Function>, StopToken,
                                    std::decay_t<Args>...>) {
    // std::bind does not work with move only types. We have to package all
    // arguments into a tuple and use std::apply to unpack them again.
    auto callable_with_token = [f = std::forward<Function>(f),
                                args = std::make_tuple(std::forward<Args>(
                                    args)...)](StopToken st) mutable {
      // Since apply takes a tuple, we need to prepend the StopToken to the
      // existing args tuple.
      std::apply(f, std::tuple_cat(std::make_tuple(st), std::move(args)));
    };
    return CreateThreadFromInvocable(options, std::move(callable_with_token));
  } else {
    // f doesn't take a StopToken. Create a lambda which does take a StopToken
    // and which will not use it. Similarly to the branch above, we need to
    // package the arguments into a tuple and use std::apply to unpack them
    // again.
    auto callable_with_token =
        [f = std::forward<Function>(f),
         args = std::make_tuple(std::forward<Args>(args)...)](
            StopToken st) mutable { std::apply(f, std::move(args)); };
    return CreateThreadFromInvocable(options, std::move(callable_with_token));
  }
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_THREAD_UTILS_H_
