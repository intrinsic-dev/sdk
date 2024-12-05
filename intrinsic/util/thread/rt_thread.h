// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_RT_THREAD_H_
#define INTRINSIC_UTIL_THREAD_RT_THREAD_H_

#include <utility>

#include "absl/status/statusor.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"
#include "intrinsic/util/thread/thread_utils.h"

namespace intrinsic {

// Creates a thread that is capable of running realtime code.
//
// The underlying thread is only truly an RT thread if the ThreadOptions
// specify it. For additional details on the threads which are created by this
// function, please see the ThreadOptions documentation.
// Note: When default constructed ThreadOptions are used consider to just use a
// plain intrinsic::Thread.
template <typename Function, typename... Args>
absl::StatusOr<Thread> CreateRealtimeCapableThread(const ThreadOptions& options,
                                                   Function&& f,
                                                   Args&&... args) {
  INTRINSIC_ASSERT_NON_REALTIME();
  return CreateThread(options, std::forward<Function>(f),
                      std::forward<Args>(args)...);
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_RT_THREAD_H_
