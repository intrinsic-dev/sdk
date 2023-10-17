// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_GRPC_CHANNEL_H_
#define INTRINSIC_UTIL_GRPC_CHANNEL_H_

#include <memory>
#include <string>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "grpcpp/channel.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic {

// A channel to an Intrinsic gRPC service at the specified address.
class Channel : public ChannelInterface {
 public:
  // Creates a channel to an Intrinsic gRPC service based on the provided
  // connection parameters.  `timeout` specifies the maximum amount of time to
  // wait for a response from the server before giving up on creating a channel.
  static absl::StatusOr<std::shared_ptr<Channel>> Make(
      const ConnectionParams& params,
      absl::Duration timeout = kGrpcClientConnectDefaultTimeout);

  // Constructs a Channel from the given gRPC channel and server instance name.
  //
  // Under certain network configurations, `server_instance_name` can be used to
  // select among multiple gRPC service instances that are routed through a
  // single `grpc_address`. If non-empty, an HTTP header metadata field
  // "x-icon-instance-name" will be added with a value of
  // `server_instance_name`.
  Channel(std::shared_ptr<grpc::Channel> channel,
          const ConnectionParams& params);

  std::shared_ptr<grpc::Channel> GetChannel() const override;

  ClientContextFactory GetClientContextFactory() const override;

 private:
  std::shared_ptr<grpc::Channel> channel_;

  // Parameters specifying how to connect to an Intrinsic gRPC service.
  ConnectionParams params_;
};

namespace icon {
using ::intrinsic::Channel;
}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_GRPC_CHANNEL_H_
