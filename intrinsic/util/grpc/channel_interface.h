// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_GRPC_CHANNEL_INTERFACE_H_
#define INTRINSIC_UTIL_GRPC_CHANNEL_INTERFACE_H_

#include <functional>
#include <memory>

#include "grpcpp/channel.h"
#include "grpcpp/client_context.h"

namespace intrinsic {

// Factory function that produces a ::grpc::ClientContext.
using ClientContextFactory =
    std::function<std::unique_ptr<::grpc::ClientContext>()>;

// Returns `std::make_unique<::grpc::ClientContext>()`.
std::unique_ptr<::grpc::ClientContext> DefaultClientContextFactory();

// Provides a channel to an ICON server.
//
class ChannelInterface {
 public:
  virtual ~ChannelInterface() {}

  // Returns a grpc::channel to the server.
  virtual std::shared_ptr<grpc::Channel> GetChannel() const = 0;

  // Returns a factory function that produces a ::grpc::ClientContext. By
  // default, uses `std::make_unique<::grpc::ClientContext>`. This may be
  // overridden in order to set client metadata, or other ClientContext
  // settings, for all ICON API requests that use this channel.
  virtual ClientContextFactory GetClientContextFactory() const {
    return DefaultClientContextFactory;
  }
};

namespace icon {
using ::intrinsic::ChannelInterface;
using ::intrinsic::ClientContextFactory;
using ::intrinsic::DefaultClientContextFactory;
}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_GRPC_CHANNEL_INTERFACE_H_
