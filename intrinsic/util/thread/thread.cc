// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread.h"

#include <sys/types.h>

#include <thread>  // NOLINT(build/c++11)

#include "absl/log/log.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/thread/thread_utils.h"

namespace intrinsic {

Thread::Thread() = default;

Thread::~Thread() {
  if (Joinable()) {
    char thread_name[GetMaxPosixThreadNameLength()] = "unknown";
    int res = pthread_getname_np(thread_impl_.native_handle(), thread_name,
                                 GetMaxPosixThreadNameLength());
    if (res != 0) {
      LOG(WARNING) << "Failed to get thread name.";
    }
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

}  // namespace intrinsic
