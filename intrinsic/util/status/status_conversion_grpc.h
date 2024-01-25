// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_GRPC_H_
#define INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_GRPC_H_

#include "absl/base/attributes.h"
#include "absl/status/status.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/support/status.h"

namespace intrinsic {

ABSL_MUST_USE_RESULT grpc::Status ToGrpcStatus(const absl::Status& status);
ABSL_MUST_USE_RESULT grpc::Status ToGrpcStatus(
    const google::rpc::Status& status);
ABSL_MUST_USE_RESULT absl::Status ToAbslStatus(const grpc::Status& status);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_GRPC_H_
