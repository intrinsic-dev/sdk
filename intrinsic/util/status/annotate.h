// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_ANNOTATE_H_
#define INTRINSIC_UTIL_STATUS_ANNOTATE_H_

#include <string_view>

#include "absl/status/status.h"
#include "intrinsic/util/status/annotate.h"

namespace intrinsic {

// Appends message to the current message in status. Does nothing if the status
// is OK.
//
// Example:
//   status.message() = "error1."
//   message = "error2."
//   resulting status.message() = "error1.; error2."
absl::Status AnnotateError(const absl::Status& status,
                           std::string_view message);

// Prepends to the current message in status. Does nothing if the status is OK.
absl::Status PrependError(const absl::Status& status, std::string_view message);
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_ANNOTATE_H_
