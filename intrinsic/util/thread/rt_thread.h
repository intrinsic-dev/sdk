// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_THREAD_RT_THREAD_H_
#define INTRINSIC_UTIL_THREAD_RT_THREAD_H_

#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "absl/status/statusor.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/thread.h"
#include "intrinsic/util/thread/thread_options.h"
#include "intrinsic/util/thread/thread_utils.h"

namespace intrinsic {

template <typename Function, typename... Args>
absl::StatusOr<Thread> CreateRealtimeThread(const ThreadOptions& options,
                                            Function&& f, Args&&... args) {
  INTRINSIC_ASSERT_NON_REALTIME();
  INTR_ASSIGN_OR_RETURN(std::thread thread,
                        CreateThread(options, std::forward<Function>(f),
                                     std::forward<Args>(args)...));
  return Thread{std::move(thread)};
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_THREAD_RT_THREAD_H_
