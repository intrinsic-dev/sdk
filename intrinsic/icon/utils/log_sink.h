// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_UTILS_LOG_SINK_H_
#define INTRINSIC_ICON_UTILS_LOG_SINK_H_

#include <cstddef>
#include <cstdint>

#include "absl/base/log_severity.h"
#include "absl/time/time.h"

namespace intrinsic::icon {

enum class LogPriority : int {
  INFO = static_cast<int>(absl::LogSeverity::kInfo),
  WARNING = static_cast<int>(absl::LogSeverity::kWarning),
  ERROR = static_cast<int>(absl::LogSeverity::kError),
};

class LogSinkInterface {
 public:
  static constexpr size_t kLogMessageMaxSize = 2048 - 1;

  struct LogEntry {
    LogPriority priority = LogPriority::INFO;
    // Nanoseconds since epoch from a monotonic system-wide clock.
    int64_t robot_timestamp_ns = 0;
    // Nanoseconds since epoch from a system-wide real-time clock.
    int64_t wall_timestamp_ns = 0;
    // File name where the log was written.
    // Must be a string that never changes.
    const char* filename = "";
    // Line number where the log was written.
    int32_t line = 0;
    // Bytes in msg not counting '\0'.
    int32_t msglen = 0;
    // Message.
    char msg[kLogMessageMaxSize + 1];
  };

  virtual ~LogSinkInterface() = default;

  // Writes incoming log entries.
  // Typically, writes to stderr.
  // Some implementations are real-time safe and may generate the message from
  // the entry in a lower-priority thread.
  // It is forbidden to call INTRINSIC_RT_LOG inside this function or call Log
  // recursively.
  virtual void Log(const LogEntry& entry) = 0;
};

// Returns the string name for priority.
const char* LogPriorityName(LogPriority priority);

// Formats a log `entry` into `buffer` which contains `buffer_size` bytes, and
// writes a null-terminated C string.
// Not real-time safe.
// Truncates entry if the buffer size is too small.
// Returns the number of characters written (excluding null termination).
// `timezone` only affects formatting of the wall timestamp, defaulting to
// UTC.
int LogEntryFormatToBuffer(char* buffer, int buffer_size,
                           const LogSinkInterface::LogEntry& entry,
                           absl::TimeZone timezone = absl::UTCTimeZone());

// A default logger class that writes the log to standard error.
class StderrLogSink : public LogSinkInterface {
 public:
  // Not real-time safe.
  void Log(const LogEntry& entry) override;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_LOG_SINK_H_
