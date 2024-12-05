// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/thread.h"

#include <sys/types.h>

#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "absl/base/thread_annotations.h"
#include "absl/container/flat_hash_map.h"
#include "absl/synchronization/mutex.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/util/thread/stop_token.h"

namespace intrinsic {

namespace {

class PerThreadStopToken {
 public:
  StopToken GetStopToken(std::thread::id tid) const {
    absl::ReaderMutexLock lock(&mutex_);
    if (auto it = stop_tokens_.find(tid); it == stop_tokens_.end()) {  // NOLINT
      return StopToken();
    } else {  // NOLINT
      return it->second;
    }
  }

  void EmplaceStopToken(std::thread::id tid, StopToken&& stop_token) {
    absl::WriterMutexLock lock(&mutex_);
    stop_tokens_[tid] = std::move(stop_token);
  }

  void EraseStopToken(std::thread::id tid) {
    absl::WriterMutexLock lock(&mutex_);
    stop_tokens_.erase(tid);
  }

 private:
  mutable absl::Mutex mutex_;
  absl::flat_hash_map<std::thread::id, StopToken> stop_tokens_
      ABSL_GUARDED_BY(mutex_);
};

static PerThreadStopToken& GetPerThreadStopState() {
  static auto* stop_state = new PerThreadStopToken();
  return *stop_state;
}

}  // namespace

Thread::Thread() = default;

Thread::~Thread() {
  if (joinable()) {
    request_stop();
    join();
  }
  EraseStopToken();
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

void Thread::SaveStopToken() noexcept {
  thread_id_ = thread_impl_.get_id();
  GetPerThreadStopState().EmplaceStopToken(thread_id_,
                                           stop_source_.get_token());
}

void Thread::EraseStopToken() noexcept {
  // This call may be a no-op if the thread has not yet started.
  GetPerThreadStopState().EraseStopToken(thread_id_);
}

}  // namespace intrinsic
