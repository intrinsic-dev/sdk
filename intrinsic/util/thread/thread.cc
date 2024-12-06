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
  if (joinable()) {
    request_stop();
    join();
  }
}

Thread::Thread(Thread&& other)
    : stop_source_{std::move(other.stop_source_)},
      thread_impl_{std::move(other.thread_impl_)} {
  std::swap(thread_id_, other.thread_id_);
}

Thread& Thread::operator=(Thread&& other) {
  if (this != &other) {
    if (joinable()) {
      request_stop();
      join();
    }
    stop_source_ = std::move(other.stop_source_);
    thread_impl_ = std::move(other.thread_impl_);
    // Swapping ensures that we guarantee that EraseStopToken() is called for
    // the `other` thread.
    std::swap(thread_id_, other.thread_id_);
  }

  return *this;
}

void Thread::join() {
  INTRINSIC_ASSERT_NON_REALTIME();
  thread_impl_.join();
}

bool Thread::joinable() const { return thread_impl_.joinable(); }

StopSource Thread::get_stop_source() noexcept { return stop_source_; }

StopToken Thread::get_stop_token() const noexcept {
  return stop_source_.get_token();
}

bool Thread::request_stop() noexcept { return stop_source_.request_stop(); }

Thread::id Thread::get_id() const noexcept { return thread_impl_.get_id(); }

Thread::native_handle_type Thread::native_handle() {
  return thread_impl_.native_handle();
}

}  // namespace intrinsic
