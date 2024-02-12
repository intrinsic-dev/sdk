// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_RPC_H_
#define INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_RPC_H_

#include "absl/status/status.h"
#include "google/rpc/status.pb.h"

namespace intrinsic {

google::rpc::Status SaveStatusAsRpcStatus(const absl::Status& status);
absl::Status MakeStatusFromRpcStatus(const google::rpc::Status& status);
absl::Status MakeStatusFromRpcStatusWithPayloads(
    const google::rpc::Status& status, const absl::Status& copy_payloads_from);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_STATUS_CONVERSION_RPC_H_
