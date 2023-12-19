// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_LOG_IF_ERROR_H_
#define INTRINSIC_UTIL_STATUS_LOG_IF_ERROR_H_

#include <utility>

#include "absl/status/status.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/util/status/status_builder.h"
#include "intrinsic/util/status/status_macros.h"

// Expects expr to yield an absl::Status or intrinsic::StatusBuilder. If the
// status is not ok, logs the status with the given severity. Note that severity
// is from the absl::LogSeverity enum.
//
// Example:
// INTR_LOG_IF_ERROR(absl::LogSeverity::kError, FuncThatYieldsStatus());
#define INTR_LOG_IF_ERROR(severity, expr)                                      \
  INTR_STATUS_MACROS_IMPL_ELSE_BLOCKER_                                        \
  if (intrinsic::status_macro_internal::StatusAdaptorForMacros status_adapter{ \
          (expr), ABSL_LOC}) {                                                 \
    /* Status of expr is OK, nothing to do */                                  \
  } else /* NOLINT */                                                          \
    intrinsic::status_macro_internal::StatusBuilderConvertOnDestroy(           \
        status_adapter.Consume().Log(severity))

// Anything below are implementation details
namespace intrinsic {
namespace status_macro_internal {

class StatusBuilderConvertOnDestroy {
 public:
  explicit StatusBuilderConvertOnDestroy(StatusBuilder&& status_builder)
      : status_builder_(std::move(status_builder)) {}

  ~StatusBuilderConvertOnDestroy() {
    absl::Status(std::move(status_builder_)).IgnoreError();
  }

 private:
  StatusBuilder status_builder_;
};

}  // namespace status_macro_internal
}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_LOG_IF_ERROR_H_
