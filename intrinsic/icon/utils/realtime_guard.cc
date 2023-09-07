// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/utils/realtime_guard.h"

#include <dlfcn.h>

#include <cstddef>

#include "absl/debugging/stacktrace.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/icon/utils/log.h"

namespace intrinsic::icon {
namespace {

struct ThreadLocalInfo {
  absl::string_view thread_name = "(not managed by utils::Thread)";
  int realtime_guard_count = 0;
  bool realtime_checker_enabled = true;
  RealTimeGuard::Reaction realtime_check_reaction = RealTimeGuard::PANIC;
};

thread_local ThreadLocalInfo s_current_thread;

}  // namespace

// Trigger a warning about an unsafe function called from real-time.
// This function disables itself (to deal with hooked system calls like
// malloc), and then either CHECK-fails or reports the violation, depending on
// the type of reaction configured.
void TriggerRealtimeCheck(const intrinsic::SourceLocation& loc) {
  if (!s_current_thread.realtime_checker_enabled ||
      !RealTimeGuard::IsRealTime() ||
      s_current_thread.realtime_check_reaction == RealTimeGuard::IGNORE) {
    return;
  }
  s_current_thread.realtime_checker_enabled = false;  // prevent recursion
  switch (s_current_thread.realtime_check_reaction) {
    case RealTimeGuard::PANIC: {
      LOG(FATAL) << "Unsafe code executed from realtime thread '"
                 << s_current_thread.thread_name << "' (" << loc.file_name()
                 << ":" << loc.line() << ").";
      break;
    }
    case RealTimeGuard::LOGE: {
      INTRINSIC_RT_LOG_THROTTLED(ERROR)
          << "Unsafe code executed from realtime thread '"
          << s_current_thread.thread_name << "' at (" << loc.file_name() << ":"
          << loc.line() << ").";
      RealTimeGuard::LogErrorBacktrace();
      break;
    }
    case RealTimeGuard::IGNORE: {
      break;
    }
  }
  s_current_thread.realtime_checker_enabled = true;
}

RealTimeGuard::RealTimeGuard(Reaction reaction) {
  prev_reaction_ = s_current_thread.realtime_check_reaction;
  s_current_thread.realtime_check_reaction = reaction;
  s_current_thread.realtime_guard_count++;
}

RealTimeGuard::~RealTimeGuard() {
  int count = s_current_thread.realtime_guard_count;
  CHECK_GT(count, 0) << "RealTimeGuard count is > 0 (" << count << ")";
  s_current_thread.realtime_guard_count--;
  s_current_thread.realtime_check_reaction = prev_reaction_;
}

bool RealTimeGuard::IsRealTime() {
  return s_current_thread.realtime_guard_count > 0;
}

void RealTimeGuard::LogErrorBacktrace() {
  // This function needs to be real-time compatible when stack is printed
  // as a non-fatal error.
  constexpr size_t kMaxFrames = 16;
  // Get the stack trace using absl instead of linux backtrace, as that
  // sometimes doesn't show the full trace.
  void* buffer[kMaxFrames];
  const int num_frames = absl::GetStackTrace(buffer, kMaxFrames, 1);
  INTRINSIC_RT_LOG(ERROR) << "Backtrace:";
  if (num_frames >= 2) {
    Dl_info info;
    for (int index = 1; index < num_frames; index++) {
      if (dladdr(buffer[index], &info) != 0 && info.dli_sname != nullptr) {
        // Note: can't use abi::__cxa_demangle as it calls malloc, use
        // absl version instead.
        const char* name = info.dli_sname;
        INTRINSIC_RT_LOG(ERROR)
            << "#" << absl::Dec(index - 1, absl::kZeroPad2) << ": '" << name
            << "' (0x" << absl::Hex(info.dli_saddr) << ").";
      } else {
        // This should only happen for functions in the main binary, which
        // shouldn't contain any relevant information for TimeSlicer code.
        INTRINSIC_RT_LOG(ERROR)
            << "#" << absl::Dec(index - 1, absl::kZeroPad2)
            << ": 'no symbol' (0x" << absl::Hex(buffer[index]) << ").";
      }
    }
  }
}

void RealTimeGuard::SetCurrentThreadName(absl::string_view thread_name) {
  s_current_thread.thread_name = thread_name;
}

}  // namespace intrinsic::icon
