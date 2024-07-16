// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_
#define INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_

#include <optional>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/release/source_location.h"

namespace intrinsic::icon {

enum class ShutdownType {
  // No shutdown was requested.
  kNotRequested = 0,
  // A signal requested shutdown, i.e. by Kubernetes.
  kSignalledRequest,
  // A user requested the shutdown, i.e. over grpc.
  kUserRequest,
};

// Initiates a shutdown. This function is signal-safe.
void ShutdownSignalHandler(int sig);

// Initiates a shutdown per request by a user. This function is signal-safe.
// `shutdown_reason` should describe why and who requested the shutdown.
// `shutdown_reason` will be printed to std::out together with `loc` so that it
// is easy to pinpoint the source of the shutdown request.
//  If `exit_code` is provided, it will be used as the exit code of the
//  shutdown.
void RequestShutdownByUser(absl::string_view shutdown_reason,
                           std::optional<int> exit_code = std::nullopt,
                           intrinsic::SourceLocation loc = INTRINSIC_LOC);

// Returns if and what kind of shutdown was requested.
ShutdownType IsShutdownRequested();

// Returns the exit code of the shutdown request.
std::optional<int> GetShutdownExitCode();

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_
