// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/log_sink.h"

#include <algorithm>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <string>

#include "absl/log/check.h"
#include "absl/time/time.h"

namespace intrinsic::icon {

const char* LogPriorityName(LogPriority priority) {
  switch (priority) {
    case LogPriority::ERROR:
      return "ERROR";
    case LogPriority::WARNING:
      return "WARNING";
    case LogPriority::INFO:
      return "INFO";
  }
}

int LogEntryFormatToBuffer(char* buffer, int buffer_size,
                           const LogSinkInterface::LogEntry& entry,
                           absl::TimeZone timezone) {
  CHECK(buffer != nullptr);
  const char* priority = LogPriorityName(entry.priority);
  absl::Duration stamp = absl::Nanoseconds(entry.robot_timestamp_ns);
  int64_t sec = stamp / absl::Seconds(1);
  int usec = (stamp - absl::Seconds(sec)) / absl::Microseconds(1);

  // Format wall timestamp.
  // Want: "0102 15:04:05.000000"
  std::string wall =
      absl::FormatTime("%m%d %H:%M:%E6S",
                       absl::FromUnixNanos(entry.wall_timestamp_ns), timezone);

  // Get the base of the filename.
  const char* base = strrchr(entry.filename, '/');
  if (base == nullptr) {
    base = entry.filename;
  } else {
    base = base + 1;
  }

  static constexpr char kFormat[] =
      "%c%s       0 %s:%d] %05" PRId64 ".%06d: %.*s\n";

  int entry_msg_size =
      std::min(entry.msglen, static_cast<int>(sizeof(entry.msg)));

  int num_chars =
      snprintf(buffer, buffer_size, kFormat, priority[0], wall.c_str(), base,
               entry.line, sec, usec, entry_msg_size, entry.msg);
  return std::min(num_chars, buffer_size - 1);
}

void StderrLogSink::Log(const LogEntry& entry) {
  char buffer[kLogMessageMaxSize] = {0};
  LogEntryFormatToBuffer(buffer, sizeof(buffer), entry);
  fprintf(stderr, "%s", buffer);
  fflush(stderr);
}

}  // namespace intrinsic::icon
