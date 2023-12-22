// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_RET_CHECK_GRPC_H_
#define INTRINSIC_UTIL_STATUS_RET_CHECK_GRPC_H_

#include <string>

#include "absl/base/log_severity.h"
#include "absl/status/status.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/util/status/ret_check.h"
#include "intrinsic/util/status/status_builder_grpc.h"
#include "intrinsic/util/status/status_macros_grpc.h"

namespace intrinsic {
namespace internal_status_macros_ret_check {

// Returns a StatusBuilder that corresponds to a `INTR_RET_CHECK` failure.
StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location);
StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           const char* condition);
StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           const char* condition,
                                           const absl::Status& s);

// Takes ownership of `condition`.  This API is a little quirky because it is
// designed to make use of the `::Check_*Impl` methods that implement `CHECK_*`
// and `DCHECK_*`.
StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           std::string* condition);

inline StatusBuilderGrpc RetCheckImplGrpc(const absl::Status& status,
                                          const char* condition,
                                          intrinsic::SourceLocation location) {
  if (ABSL_PREDICT_TRUE(status.ok())) {
    return StatusBuilderGrpc(StatusBuilder(absl::OkStatus(), location));
  }
  return RetCheckFailSlowPathGrpc(location, condition, status);
}

}  // namespace internal_status_macros_ret_check
}  // namespace intrinsic

#define INTR_RET_CHECK_GRPC(cond)                        \
  while (ABSL_PREDICT_FALSE(!(cond)))                    \
  return ::intrinsic::internal_status_macros_ret_check:: \
      RetCheckFailSlowPathGrpc(INTRINSIC_LOC, #cond)

#define INTR_RET_CHECK_FAIL_GRPC()                       \
  return ::intrinsic::internal_status_macros_ret_check:: \
      RetCheckFailSlowPathGrpc(INTRINSIC_LOC)

// Takes an expression returning absl::Status and asserts that the status is
// `ok()`.  If not, it returns an internal error.
//
// This is similar to `INTR_RETURN_IF_ERROR` in that it propagates errors.  The
// difference is that it follows the behavior of `INTR_RET_CHECK`, returning an
// internal error (wrapping the original error text), including the filename and
// line number, and logging a stack trace.
//
// This is appropriate to use to write an assertion that a function that returns
// `absl::Status` cannot fail, particularly when the error code itself should
// not be surfaced.
#define INTR_RET_CHECK_OK_GRPC(status)                                     \
  INTR_RETURN_IF_ERROR_GRPC(                                               \
      ::intrinsic::internal_status_macros_ret_check::RetCheckImplGrpc(     \
          ::intrinsic::internal_status_macros_ret_check::AsStatus(status), \
          #status, INTRINSIC_LOC))

#endif  // INTRINSIC_UTIL_STATUS_RET_CHECK_GRPC_H_
