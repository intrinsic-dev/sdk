// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_RELEASE_STATUS_HELPERS_H_
#define INTRINSIC_ICON_RELEASE_STATUS_HELPERS_H_

#include "absl/base/log_severity.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "google/rpc/status.pb.h"

// Early-returns the status if it is in error; otherwise, proceeds.
//
// The argument expression is guaranteed to be evaluated exactly once.
#define INTRINSIC_RETURN_IF_ERROR(__status) \
  do {                                      \
    auto status = __status;                 \
    if (!status.ok()) {                     \
      return status;                        \
    }                                       \
  } while (false)

// Identifier concatenation helper macros.
#define INTRINSIC_MACRO_CONCAT_INNER(__x, __y) __x##__y
#define INTRINSIC_MACRO_CONCAT(__x, __y) INTRINSIC_MACRO_CONCAT_INNER(__x, __y)

// Implementation of INTRINSIC_ASSIGN_OR_RETURN that uses a unique temporary
// identifier for avoiding collision in the enclosing scope.
#define INTRINSIC_ASSIGN_OR_RETURN_IMPL(__lhs, __rhs, __name) \
  auto __name = (__rhs);                                      \
  if (!__name.ok()) {                                         \
    return __name.status();                                   \
  }                                                           \
  __lhs = std::move(__name.value());

// Early-returns the status if it is in error; otherwise, assigns the
// right-hand-side expression to the left-hand-side expression.
//
// The right-hand-side expression is guaranteed to be evaluated exactly once.
#define INTRINSIC_ASSIGN_OR_RETURN(__lhs, __rhs) \
  INTRINSIC_ASSIGN_OR_RETURN_IMPL(               \
      __lhs, __rhs, INTRINSIC_MACRO_CONCAT(__status_or_value, __COUNTER__))

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
