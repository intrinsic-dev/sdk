// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_RPC_STATUS_CONVERSION_H_
#define INTRINSIC_UTIL_STATUS_RPC_STATUS_CONVERSION_H_

#include "absl/status/status.h"
#include "google/rpc/status.pb.h"
#include "intrinsic/util/status/rpc_status_conversion.h"

namespace intrinsic {

google::rpc::Status SaveStatusAsRpcStatus(const absl::Status& status);
absl::Status MakeStatusFromRpcStatus(const google::rpc::Status& status);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_RPC_STATUS_CONVERSION_H_
