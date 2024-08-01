// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/utils/realtime_guard.h"

#include <dlfcn.h>

#include "absl/log/check.h"
#include "absl/log/log.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/icon/utils/log.h"
#include "intrinsic/icon/utils/realtime_stack_trace.h"

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
          << loc.line() << "). Stack trace: \n"
          << absl::string_view(GenerateRtErrorStackTrace());

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

void RealTimeGuard::SetCurrentThreadName(absl::string_view thread_name) {
  s_current_thread.thread_name = thread_name;
}

}  // namespace intrinsic::icon
