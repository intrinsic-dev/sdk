// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_GRPC_GRPC_H_
#define INTRINSIC_UTIL_GRPC_GRPC_H_

#include <cstdint>
#include <memory>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpcpp/grpcpp.h"

namespace intrinsic {

// Constant `kGrpcClientConnectDefaultTimeout` is the default timeout for the
// initial GRPC connection made by client libraries.
constexpr absl::Duration kGrpcClientConnectDefaultTimeout = absl::Seconds(5);

/**
 * Create a grpc server using the listen port on the default interface
 * and the set of services provided
 */
absl::StatusOr<std::unique_ptr<::grpc::Server>> CreateServer(
    uint16_t listen_port, const std::vector<::grpc::Service*>& services);

/**
 * Apply the default configuration of our project to the given ClientContext.
 */
void ConfigureClientContext(::grpc::ClientContext* client_context);

/**
 * Wait for a newly created channel to be connected
 */
absl::Status WaitForChannelConnected(absl::string_view address,
                                     std::shared_ptr<::grpc::Channel> channel,
                                     absl::Time deadline = absl::Now());

// Get recommended default gRPC channel arguments.
::grpc::ChannelArguments DefaultGrpcChannelArgs();

// Get gRPC channel arguments with unlimited send/receive message size.
// This also includes all settings from DefaultGrpcChannelArgs(). This can be
// used for services that send large messages, e.g., the geometry service.
::grpc::ChannelArguments UnlimitedMessageSizeGrpcChannelArgs();

/**
 * Apply default configuration of our project and create a new channel
 */
absl::StatusOr<std::shared_ptr<::grpc::Channel>> CreateClientChannel(
    absl::string_view address, absl::Time deadline,
    const ::grpc::ChannelArguments& channel_args = DefaultGrpcChannelArgs(),
    bool use_default_application_credentials = false);

// Parameters to configure the shutdown behavior of a gRPC server.
struct ShutdownParams {
  // Duration to wait for the grpc's health service state (if relevant) to
  // propagate to the load balancers.
  absl::Duration health_grace_duration;
  // Timeout passed into grpc::Server::Shutdown on a sigterm.
  absl::Duration shutdown_timeout;

  // Returns params that aggressively shutdowns the server.
  static ShutdownParams Aggressive();
};

// Registers a custom signal handler for SIGTERM, serves the server and blocks
// till it is shutdown. The custom handler is left registered when the function
// returns.
//
// `handlers_registered` notification is triggered once the signal handler is
// registered. This is mainly useful in unit tests to know when it is okay to
// raise a SIGTERM signal.
//
// Returns an error if registering the signal handler fails.
//
// Typical usage:
// ```
//   int main() {
//      auto server = intrinsic::CreateServer(...);
//      absl::Notification registered;
//      QCHECK_OK(RegisterSignalHandlerAndWait(server.get(),
//                ShutdownParams{...}, registered));
//      return EXIT_SUCCESS;
//   }
// ```
absl::Status RegisterSignalHandlerAndWait(
    ::grpc::Server* server, const ShutdownParams& params,
    absl::Notification& handlers_registered);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_GRPC_GRPC_H_
