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
  if (Joinable()) {
    RequestStop();
    Join();
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
    if (Joinable()) {
      RequestStop();
      Join();
    }
    stop_source_ = std::move(other.stop_source_);
    thread_impl_ = std::move(other.thread_impl_);
    std::swap(thread_id_, other.thread_id_);
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

void Thread::SaveStopToken() noexcept {
  thread_id_ = thread_impl_.get_id();
  GetPerThreadStopState().EmplaceStopToken(thread_id_,
                                           stop_source_.get_token());
}

void Thread::EraseStopToken() noexcept {
  GetPerThreadStopState().EraseStopToken(thread_id_);
}

bool ThisThreadStopRequested() {
  // We tried thread_local storage here, but it did not work and lead to
  // spurious crashes.
  const StopToken kStopToken =
      GetPerThreadStopState().GetStopToken(std::this_thread::get_id());
  return kStopToken.stop_requested();
}

}  // namespace intrinsic
