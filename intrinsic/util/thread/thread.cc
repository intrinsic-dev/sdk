// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread.h"

#include <sys/types.h>

#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/thread/stop_token.h"

namespace intrinsic {

Thread::Thread() = default;

Thread::~Thread() {
  if (Joinable()) {
    RequestStop();
    Join();
  }
}

Thread& Thread::operator=(Thread&& other) {
  if (this != &other) {
    if (Joinable()) {
      RequestStop();
      Join();
    }
    stop_source_ = std::move(other.stop_source_);
    thread_impl_ = std::move(other.thread_impl_);
  }

  return *this;
}

void Thread::Join() {
  INTRINSIC_ASSERT_NON_REALTIME();
  thread_impl_.join();
}

bool Thread::Joinable() const { return thread_impl_.joinable(); }

StopSource Thread::GetStopSource() noexcept { return stop_source_; }

StopToken Thread::GetStopToken() const noexcept {
  return stop_source_.get_token();
}

bool Thread::RequestStop() noexcept { return stop_source_.request_stop(); }

}  // namespace intrinsic
