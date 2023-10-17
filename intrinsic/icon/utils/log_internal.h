// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_LOG_INTERNAL_H_
#define INTRINSIC_ICON_UTILS_LOG_INTERNAL_H_

#include <errno.h>
#include <unistd.h>

#include <atomic>
#include <cstdint>
#include <memory>
#include <optional>

#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/icon/utils/fixed_string.h"
#include "intrinsic/icon/utils/log_sink.h"

namespace intrinsic::icon {
namespace internal {

// Returns monotonic time in robot_timestamp_ns and wall time
// in wall_timestamp_ns (nanoseconds since epoch).
// The default get time function for logging.
void LogGetTime(int64_t* robot_timestamp_ns, int64_t* wall_timestamp_ns);

// A counter for a logging call site that helps merge repeated calls to one
// log message within a certain `kSpamPeriodNanoseconds`.
// Thread-compatible.
struct LogThrottler {
 public:
  struct Result {
    // Contains the number of log calls that should be reported in one log
    // message.
    int32_t num_calls_merged = 0;
    // If multiple log calls were merged, the time period from the oldest call
    // that was throttled to the current one.
    int64_t period_nanoseconds = 0;
    int64_t robot_timestamp_ns = 0;
    int64_t wall_timestamp_ns = 0;
  };

  using GetTimeFunction = void (*)(int64_t* robot_timestamp_ns,
                                   int64_t* wall_timestamp_ns);

  // Log calls within this time period are throttled by the
  // INTRINSIC_RT_LOG_THROTTLED macros. INTRINSIC_RT_LOG_THROTTLED macros count
  // repetitions and report the number of duplicates.
  static constexpr int64_t kSpamPeriodNanoseconds = 750000000;
  // Maximum number of duplicates to drop before logging again.
  static constexpr int kMaxDeduplicationCount = 1000;

  // Counts calls from a INTRINSIC_RT_LOG_THROTTLED call site and decides if we
  // should log.
  // Returns nullopt if the call should be ignored.
  std::optional<Result> Tick(GetTimeFunction get_time_function = LogGetTime);

 private:
  // Number of log calls that have not been reported yet.
  std::atomic<int32_t> num_calls_merged = 0;
  // Time of oldest log call that was not reported.
  std::atomic<int64_t> first_log_time = 0;
  // Time of the previous log call.
  std::atomic<int64_t> last_log_time = 0;
};

}  // namespace internal

// Holds global and thread-local logger and configuration.
class GlobalLogContext {
 public:
  using GetTimeFunction =
      intrinsic::icon::internal::LogThrottler::GetTimeFunction;

  // Sets or resets the logger for this thread.
  // It only affects the current thread, so it is thread-safe.
  // Not real-time safe.
  // If `logger` is nullptr, resets to the fallback StderrLogSink logger.
  static void SetThreadLocalLogSink(std::unique_ptr<LogSinkInterface> logger);

  // Gets the current logger for this thread (the one set by
  // SetThreadLocalLogSink()). If none was set, returns the fallback
  // StderrLogSink, which is not real-time safe.
  static inline LogSinkInterface& GetThreadLocalLogSinkOrFallback();

  // Gets the current time in nanoseconds since some point in history.
  static void GetTime(int64_t* robot_timestamp_ns, int64_t* wall_timestamp_ns) {
    (*GetGetTimeFunction())(robot_timestamp_ns, wall_timestamp_ns);
  }

  // Sets the getTime function.
  // This allows the use of a different clock for timestamps.
  // Not thread-safe, should be called only at startup.
  // The first argument of `get_time` is the robot time (intrinsic::Clock,
  // monotonic) and the second is the wall time.
  static void SetTimeFunction(GetTimeFunction get_time);

 private:
  // Returns a pointer to the GetTimeFunction.
  // We use this (as opposed to a static member variable) because this
  // guarantees func is initialized before use.
  static GetTimeFunction* GetGetTimeFunction() {
    static GetTimeFunction s_get_time = &intrinsic::icon::internal::LogGetTime;
    return &s_get_time;
  }
};

namespace internal {

// Generates a text log message from integer, floating-point and string-like
// data types (by using absl::AlphaNum).
class LogEntryBuilder {
 public:
  static LogEntryBuilder Create(LogPriority priority,
                                LogThrottler::Result throttler_result,
                                intrinsic::SourceLocation source_location) {
    return {priority, throttler_result, source_location};
  }

  static LogEntryBuilder Create(LogPriority priority,
                                intrinsic::SourceLocation source_location) {
    LogThrottler::Result throttler_result;
    throttler_result.num_calls_merged = 1;
    GlobalLogContext::GetTime(&throttler_result.robot_timestamp_ns,
                              &throttler_result.wall_timestamp_ns);
    return Create(priority, throttler_result, source_location);
  }

  LogEntryBuilder& operator<<(const absl::AlphaNum& a) {
    message_.append(a.Piece());
    return *this;
  }

  LogSinkInterface::LogEntry GetEntry() const {
    LogSinkInterface::LogEntry entry;
    entry.priority = priority_;
    entry.filename = source_location_.file_name();
    entry.line = source_location_.line();
    return entry;
  }

  absl::string_view message() const { return message_; }
  LogPriority priority() const { return priority_; }
  LogThrottler::Result throttler_result() const { return throttler_result_; }

 private:
  LogEntryBuilder(LogPriority priority, LogThrottler::Result throttler_result,
                  intrinsic::SourceLocation source_location)
      : priority_(priority),
        source_location_(source_location),
        throttler_result_(throttler_result) {}

  LogPriority priority_;
  intrinsic::SourceLocation source_location_;
  LogThrottler::Result throttler_result_;
  FixedString<LogSinkInterface::kLogMessageMaxSize + 1> message_;
};

// Passes log message to the sink.
// There is one object for a logging call site, so it could in the future do
// filtering.
//
// operator+= actually logs the message, it is chosen only to have lower
// precedence and be executed last, so the execution order is:
// 1. LogThrottler::Tick does throttling.
// 2. LogCommand() (can in the future be used for filtering)
// 3. LogMessageGenerator() to write the priority.
// 4. Multiple operator<< calls to convert pieces to string and concatenate
//    the text message.
// 5. operator+= writes the log entry to thread-local LogSink.
// 6. If LogSink is RealtimeLogSink, GlobalLogSink eventually reads from the
//    queue and writes to stderr. Fall back StderrLogSink writes directly.
class LogClient {
 public:
  void operator+=(LogEntryBuilder& builder) const;
};

}  // namespace internal
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_LOG_INTERNAL_H_
