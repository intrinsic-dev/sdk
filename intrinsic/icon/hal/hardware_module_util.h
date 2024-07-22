// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_UTIL_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_UTIL_H_

#include "absl/strings/str_format.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state.fbs.h"

namespace intrinsic_fbs {

template <typename Sink>
void AbslStringify(Sink& sink, StateCode e) {
  absl::Format(&sink, "%s", EnumNameStateCode(e));
}

}  // namespace intrinsic_fbs

namespace intrinsic::icon {

enum class TransitionGuardResult { kNoOp, kAllowed, kProhibited };

// Returns whether the transition from `from` to `to` is allowed, prohibited or
// a no-op (e.g. from MotionEnabled to MotionEnabling).
TransitionGuardResult HardwareModuleTransitionGuard(
    intrinsic_fbs::StateCode from, intrinsic_fbs::StateCode to);

// Exit codes that a HWM process uses to indicate special results to
// the caller.
enum class HardwareModuleExitCode {
  // HWM shutdown normally.
  kNormalShutdown = 0,
  // HWM reported a fatal fault during initialization.
  kFatalFaultDuringInit = 111,

  // HWM reported a fatal fault during execution.
  kFatalFaultDuringExec = 112,
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_UTIL_H_
