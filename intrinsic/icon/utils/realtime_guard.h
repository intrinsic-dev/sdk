// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_REALTIME_GUARD_H_
#define INTRINSIC_ICON_UTILS_REALTIME_GUARD_H_

#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic::icon {

// RealTimeGuard is a debugging tool to mark a section of code as real-time
// (RT). Real-time unsafe code can then assert that it is not called from a
// section that is real-time guarded. For example:
//
// Thread t([]()->int {
//
//   // Here we can still use RT-unsafe code like malloc(), new...
//   Initialize();
//
//   // From here, this thread must have real time guarantees.
//   RealTimeGuard guard;
//
//   while (IsExitRequested()) {
//     // do something here
//     return 0;
//   }
// }));
// t.Start("my thread");
// t.Join();
//
// RealTimeGuard is nestable.
//
// Also see RealTimeGuard::IsRealTime().
// Also see INTRINSIC_ASSERT_NON_REALTIME macro.
class RealTimeGuard {
 public:
  // Types of reactions to unsafe functions being called from a real-time
  // thread.
  enum Reaction {
    IGNORE = 0,  // Do nothing, silently proceed
    LOGE = 1,    // Log the function call as an error and proceed
    PANIC = 2    // CHECK-fail and terminate the process immediately
  };
  /**
   * Enters the realtime section.
   *
   * CHECK-fails if unsafe functions are called from this thread.
   */
  RealTimeGuard() : RealTimeGuard(PANIC) {}

  /**
   * Enters the realtime section.
   *
   * @param reaction The type of reaction to unsafe functions being called
   * from this thread.
   */
  explicit RealTimeGuard(Reaction reaction);

  /**
   * Exits the realtime section.
   */
  ~RealTimeGuard();

  /**
   * Returns whether the current thread is in a real-time section marked by
   * RealTimeGuard.
   * @return true if the current thread is in a real-time section, false
   * otherwise.
   * @see RealTimeGuard
   */
  static bool IsRealTime();

  // Print a simple backtrace.
  // Used by RealtimeChecker::trigger(), public only for testing purposes.
  // This function does not allocate and is real-time compatible.
  static void LogErrorBacktrace();

  // Optional, only results in `thread_name` being shown in warnings and errors.
  // `thread_name` must outlive `RealTimeGuard`.
  static void SetCurrentThreadName(absl::string_view thread_name);

 private:
  Reaction prev_reaction_;
};

// Trigger a warning about an unsafe function called from real-time.
// This function disables itself (to deal with hooked system calls like
// malloc), and then either CHECK-fails or reports the violation, depending on
// the type of reaction configured.
void TriggerRealtimeCheck(const intrinsic::SourceLocation& loc);

}  // namespace intrinsic::icon

/**
 * Checks that the current thread is not a realtime thread. Use
 * RealTimeGuard to mark that a section of code must have real-time
 * guarantees. If the current thread has realtime guarantees, this macro will
 * Panic.
 *
 * @code
 * void RtUnsafeCode() {
 *   // this code is not rt-safe, so we assert we're not in a realtime section
 *   INTRINSIC_ASSERT_NON_REALTIME()
 *   // do things that don't have realtime guarantees here...
 * }
 *
 * void RealtimeGuarantee() {
 *   // this code must have realtime guarantees, mark it as such
 *   RealTimeGuard guard;
 *   // do realtime stuff here...
 * }
 * @endcode
 *
 */
static inline void INTRINSIC_ASSERT_NON_REALTIME(
    const intrinsic::SourceLocation& loc =
        intrinsic::SourceLocation::current()) {
  intrinsic::icon::TriggerRealtimeCheck(loc);
}

#endif  // INTRINSIC_ICON_UTILS_REALTIME_GUARD_H_
