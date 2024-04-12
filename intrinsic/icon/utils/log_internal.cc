// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/log_internal.h"

#include <bits/time.h>
#include <ctype.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <memory>
#include <optional>
#include <utility>

#include "absl/log/log.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/log_sink.h"

namespace intrinsic::icon {
namespace internal {

struct LoggerThreadInfo {
  // If nullptr, use GetFallbackLogSink() instead.
  std::unique_ptr<LogSinkInterface> logger;
  // Existing log entry in call stack to detect recursive logging.
  LogSinkInterface::LogEntry* log_entry = nullptr;
};

}  // namespace internal

// Thread local info.
// Note: In threads created via intrinsic::Thread this is allocated at thread
// creation time via the call to GlobalLogContext::SetThreadLocalLogSink from
// Thread::setup(). Therefore these will not allocate in runtime threads once
// the thread has started.
static thread_local internal::LoggerThreadInfo s_thread_info;

//-----------------------------------------------------------------------------

static inline internal::LoggerThreadInfo& GetThreadInfo() {
  internal::LoggerThreadInfo& info = s_thread_info;
  return info;
}

// RT safe after static initialization by InternalInit.
LogSinkInterface& GetFallbackLogSink() INTRINSIC_SUPPRESS_REALTIME_CHECK {
  static StderrLogSink* s_default_logger = new StderrLogSink;
  return *s_default_logger;
}

bool InternalInit() {
  GetFallbackLogSink();
  return true;
}

// This ensures all main-thread allocations occur before main() begins.
// Static initialization order does not matter, as `s_default_logger` is
// accessible only through the functions that ensure they exist and are
// initialized.
static bool s_initialized = InternalInit();

inline LogSinkInterface& GlobalLogContext::GetThreadLocalLogSinkOrFallback()
    INTRINSIC_SUPPRESS_REALTIME_CHECK {
  if (GetThreadInfo().logger == nullptr) {
    thread_local bool has_been_warned = false;
    if (!has_been_warned) {
      LOG(WARNING) << "PUBLIC: Potential real-time violation: Using "
                      "INTRINSIC_RT_LOG without "
                      "previous call to RtLogInitForThisThread().";
      has_been_warned = true;
    }
    return GetFallbackLogSink();
  }
  return *GetThreadInfo().logger;
}

void GlobalLogContext::SetThreadLocalLogSink(
    std::unique_ptr<LogSinkInterface> logger) {
  GetThreadInfo().logger = std::move(logger);
}

void GlobalLogContext::SetTimeFunction(void (*get_time)(int64_t*, int64_t*)) {
  *GetGetTimeFunction() = get_time != nullptr ? get_time : internal::LogGetTime;
}

namespace internal {

void LogGetTime(int64_t* robot_timestamp_ns, int64_t* wall_timestamp_ns) {
  struct timespec ts_robot;
  struct timespec ts_wall;
  clock_gettime(CLOCK_MONOTONIC, &ts_robot);
  clock_gettime(CLOCK_REALTIME, &ts_wall);

  *robot_timestamp_ns =
      absl::ToInt64Nanoseconds(absl::DurationFromTimespec(ts_robot));
  *wall_timestamp_ns =
      absl::ToInt64Nanoseconds(absl::DurationFromTimespec(ts_wall));
}

std::optional<LogThrottler::Result> LogThrottler::Tick(
    GetTimeFunction get_time_function) {
  Result result;
  get_time_function(&result.robot_timestamp_ns, &result.wall_timestamp_ns);
  if (num_calls_merged == 0) {
    // Record first log time.
    first_log_time = result.robot_timestamp_ns;
  }
  ++num_calls_merged;
  result.period_nanoseconds = result.robot_timestamp_ns - first_log_time;
  result.num_calls_merged = num_calls_merged;
  int64_t delta = result.robot_timestamp_ns - last_log_time;
  if (num_calls_merged >= kMaxDeduplicationCount ||
      delta >= kSpamPeriodNanoseconds) {
    // Log and reset.
    last_log_time = result.robot_timestamp_ns;
    num_calls_merged = 0;
    return result;
  }
  return {};
}

void LogClient::operator+=(LogEntryBuilder& builder) const {
  int save_errno = errno;
  if (builder.throttler_result().num_calls_merged > 1) {
    float period_seconds = absl::ToDoubleSeconds(
        absl::Nanoseconds(builder.throttler_result().period_nanoseconds));
    builder << " (repeated " << builder.throttler_result().num_calls_merged
            << " times in " << period_seconds << "s)";
  }
  LogSinkInterface::LogEntry entry = builder.GetEntry();
  std::memset(entry.msg, 0, sizeof(entry.msg));
  entry.robot_timestamp_ns = builder.throttler_result().robot_timestamp_ns;
  entry.wall_timestamp_ns = builder.throttler_result().wall_timestamp_ns;
  entry.msglen = std::min(sizeof(entry.msg) - 1, builder.message().size());
  std::memcpy(entry.msg, builder.message().data(), entry.msglen);

  // Strip trailing newlines and spaces.
  int msglen = entry.msglen;
  while (msglen > 0 && isspace(entry.msg[msglen - 1])) {
    --msglen;
  }
  entry.msg[msglen] = 0;  // null terminate so logWrite() can use strchr etc.
  entry.msglen = msglen;

  // Fail on recursive log calls.
  internal::LoggerThreadInfo& info = GetThreadInfo();
  if (info.log_entry != nullptr) {
    [&]() INTRINSIC_SUPPRESS_REALTIME_CHECK {
      LOG(FATAL) << "Recursive INTRINSIC_RT_LOG log call at " << entry.filename
                 << " line " << entry.line;
    }();
  }
  info.log_entry = &entry;
  GlobalLogContext::GetThreadLocalLogSinkOrFallback().Log(entry);
  info.log_entry = nullptr;

  errno = save_errno;
}

}  // namespace internal
}  // namespace intrinsic::icon
