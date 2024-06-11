// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_
#define INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_

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
void RequestShutdownByUser();

// Returns if and what kind of shutdown was requested.
ShutdownType IsShutdownRequested();

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_SHUTDOWN_SIGNALS_H_
