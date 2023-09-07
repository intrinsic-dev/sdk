// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/utils/realtime_log_sink.h"

#include <errno.h>
#include <pthread.h>
#include <sched.h>

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <memory>
#include <ostream>
#include <thread>  // NOLINT(build/c++11)
#include <utility>

#include "absl/base/thread_annotations.h"
#include "absl/container/flat_hash_map.h"
#include "absl/log/log.h"
#include "absl/synchronization/mutex.h"
#include "absl/synchronization/notification.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/remote_trigger/binary_futex.h"
#include "intrinsic/icon/utils/log_sink.h"
#include "intrinsic/icon/utils/realtime_guard.h"
#include "intrinsic/platform/common/buffers/realtime_write_queue.h"

namespace intrinsic::icon {

class GlobalLogSink {
 public:
  GlobalLogSink()
      : reader_thread_([this]() {
          reader_thread_started_.Notify();
          Run();
        }) {
    // Must not run at realtime priority.
    sched_param scheduler_param{.sched_priority = 0};
    int policy = SCHED_OTHER;
    if (int errnum = pthread_setschedparam(reader_thread_.native_handle(),
                                           policy, &scheduler_param) != 0;
        errnum != 0) {
      LOG(FATAL) << "Failed to set GlobalLogSink thread parameters: "
                 << std::strerror(errnum);
    }
    // Must be at most 16 characters.
    pthread_setname_np(reader_thread_.native_handle(), "GlobalLogSink");
    reader_thread_started_.WaitForNotification();
  }
  ~GlobalLogSink() {
    stop_reader_thread_ = true;
    (void)notify_reader_.Post();
    if (reader_thread_.joinable()) reader_thread_.join();
  }

  RealtimeWriteQueue<LogSinkInterface::LogEntry>::RtWriter* CreateWriter() {
    absl::MutexLock lock(&mutex_);
    auto queue =
        std::make_unique<RealtimeWriteQueue<LogSinkInterface::LogEntry>>(
            /*capacity=*/1000);
    auto* writer = &queue->Writer();
    queues_[writer] = std::move(queue);
    return writer;
  }

  void RemoveWriter(
      RealtimeWriteQueue<LogSinkInterface::LogEntry>::RtWriter* writer) {
    absl::MutexLock lock(&mutex_);
    FlushAndRemoveWriter(writer);
  }

  void Run() {
    while (true) {
      (void)notify_reader_.WaitFor(absl::InfiniteDuration());
      if (stop_reader_thread_) break;
      absl::MutexLock lock(&mutex_);
      for (auto& [_, queue] : queues_) {
        if (queue->Reader().Empty()) continue;
        LogSinkInterface::LogEntry entry;
        // Do not wait.
        auto result =
            queue->Reader().ReadWithTimeout(entry, absl::InfinitePast());
        if (result != ReadResult::kConsumed) continue;
        char buffer[LogSinkInterface::kLogMessageMaxSize];
        LogEntryFormatToBuffer(buffer, sizeof(buffer), entry);
        fprintf(stderr, "%s", buffer);
        fflush(stderr);
        if (!queue->Reader().Empty()) (void)notify_reader_.Post();
      }
    }
    absl::MutexLock lock(&mutex_);
    while (!queues_.empty()) {
      FlushAndRemoveWriter(queues_.begin()->first);
    }
  }

  // RT safe.
  void Notify() { (void)notify_reader_.Post(); }

 private:
  void FlushAndRemoveWriter(
      RealtimeWriteQueue<LogSinkInterface::LogEntry>::RtWriter* writer)
      ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
    writer->Close();
    auto& queue = queues_.find(writer)->second;
    while (!queue->Reader().Empty()) {
      LogSinkInterface::LogEntry entry;
      auto result =
          queue->Reader().ReadWithTimeout(entry, absl::InfinitePast());
      if (result != ReadResult::kConsumed) break;
      char buffer[LogSinkInterface::kLogMessageMaxSize];
      LogEntryFormatToBuffer(buffer, sizeof(buffer), entry);
      fprintf(stderr, "%s", buffer);
      fflush(stderr);
    }
    queues_.erase(writer);
  }

  absl::Mutex mutex_;
  absl::flat_hash_map<
      RealtimeWriteQueue<LogSinkInterface::LogEntry>::RtWriter*,
      std::unique_ptr<RealtimeWriteQueue<LogSinkInterface::LogEntry>>>
      queues_ ABSL_GUARDED_BY(mutex_);
  absl::Notification reader_thread_started_;
  std::atomic<bool> stop_reader_thread_ = false;
  BinaryFutex notify_reader_;
  // We cannot use intrinsic::Thread here to avoid cyclic dependency.
  std::thread reader_thread_;
};

GlobalLogSink& GetGlobalLogSink() {
  // Avoid destruction of global object.
  static GlobalLogSink* global_log_sink = new GlobalLogSink();
  return *global_log_sink;
}

RealtimeLogSink::RealtimeLogSink() {
  INTRINSIC_ASSERT_NON_REALTIME();
  writer_ = GetGlobalLogSink().CreateWriter();
}

RealtimeLogSink::~RealtimeLogSink() {
  INTRINSIC_ASSERT_NON_REALTIME();
  GetGlobalLogSink().RemoveWriter(writer_);
}

void RealtimeLogSink::Log(const LogEntry& entry) {
  if (!writer_->Closed()) {
    (void)writer_->Write(entry);
    GetGlobalLogSink().Notify();
  }
}

}  // namespace intrinsic::icon
