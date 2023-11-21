// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/grpc/channel_interface.h"

#include <memory>

#include "grpcpp/client_context.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic {

std::unique_ptr<::grpc::ClientContext> DefaultClientContextFactory() {
  auto client_context = std::make_unique<::grpc::ClientContext>();
  ConfigureClientContext(client_context.get());
  return client_context;
}

}  // namespace intrinsic
