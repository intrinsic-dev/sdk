// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_RELEASE_STATUS_HELPERS_H_
#define INTRINSIC_ICON_RELEASE_STATUS_HELPERS_H_

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "google/rpc/status.pb.h"

namespace intrinsic {

google::rpc::Status SaveStatusAsRpcStatus(const absl::Status& status);
absl::Status MakeStatusFromRpcStatus(const google::rpc::Status& status);

// Appends message to the current message in status. Does nothing if the status
// is OK.
//
// Example:
//   status.message() = "error1."
//   message = "error2."
//   resulting status.message() = "error1.; error2."
absl::Status AnnotateError(const absl::Status& status,
                           absl::string_view message);

}  // namespace intrinsic

#endif  // INTRINSIC_ICON_RELEASE_STATUS_HELPERS_H_
