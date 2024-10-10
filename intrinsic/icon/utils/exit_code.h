// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_EXIT_CODE_H_
#define INTRINSIC_ICON_UTILS_EXIT_CODE_H_

namespace intrinsic::icon {

// Exit codes for ICON MainLoop to explain the reason for the exit.
// init_icon.go may choose to restart MainLoop on these exit codes.
enum class ExitCode {
  // Fatal fault during initialization.
  kFatalFaultDuringInit = 111,
  // Fatal fault during execution.
  kFatalFaultDuringExec = 112,
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_EXIT_CODE_H_
