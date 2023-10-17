// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/grpc/channel_interface.h"

#include <memory>

#include "grpcpp/client_context.h"

namespace intrinsic {

std::unique_ptr<::grpc::ClientContext> DefaultClientContextFactory() {
  return std::make_unique<::grpc::ClientContext>();
}

}  // namespace intrinsic
