// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_REALTIME_LOG_SINK_H_
#define INTRINSIC_ICON_UTILS_REALTIME_LOG_SINK_H_

#include <cstddef>

#include "intrinsic/icon/utils/log_sink.h"
#include "intrinsic/platform/common/buffers/realtime_write_queue.h"

namespace intrinsic::icon {

// A real-time safe log sink that writes to std::cerr.
// When there are multiple threads, each should create a thread-local object.
// Messages are buffered by a single, global non-RT thread and written out
// message by message.
class RealtimeLogSink : public LogSinkInterface {
 public:
  // Not RT safe.
  RealtimeLogSink();

  // Not RT safe.
  // Blocks until the log buffer has been written.
  ~RealtimeLogSink() override;

  // RT safe.
  // Not thread-safe, but concurrent use is allowed when each thread uses a
  // separate RealtimeLogSink object.
  // Messages reaching or exceeding kMessageMaxSize will be truncated.
  // If the buffer is full, messages may be dropped.
  void Log(const LogEntry& entry) override;

 private:
  RealtimeWriteQueue<LogEntry>::RtWriter* writer_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_REALTIME_LOG_SINK_H_
