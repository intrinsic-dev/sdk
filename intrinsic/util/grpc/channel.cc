// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/grpc/channel.h"

#include <memory>
#include <utility>

#include "absl/status/statusor.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpcpp/channel.h"
#include "intrinsic/util/grpc/connection_params.h"
#include "intrinsic/util/grpc/grpc.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

absl::StatusOr<std::shared_ptr<Channel>> Channel::Make(
    const ConnectionParams& params, absl::Duration timeout) {
  // Set the max message size to unlimited to allow longer trajectories.
  // Please check with the motion team before changing the value (see
  // b/275280379).
  INTR_ASSIGN_OR_RETURN(
      std::shared_ptr<grpc::Channel> channel,
      CreateClientChannel(params.address, absl::Now() + timeout,
                          UnlimitedMessageSizeGrpcChannelArgs()));
  return std::make_shared<Channel>(channel, params);
}

std::shared_ptr<grpc::Channel> Channel::GetChannel() const { return channel_; }

ClientContextFactory Channel::GetClientContextFactory() const {
  return [params = params_]() {
    auto context = std::make_unique<::grpc::ClientContext>();
    ConfigureClientContext(context.get());
    for (const auto& [header, value] : params.Metadata()) {
      context->AddMetadata(header, value);
    }
    return context;
  };
}

Channel::Channel(std::shared_ptr<grpc::Channel> channel,
                 const ConnectionParams& params)
    : channel_(std::move(channel)), params_(params) {}

}  // namespace intrinsic
