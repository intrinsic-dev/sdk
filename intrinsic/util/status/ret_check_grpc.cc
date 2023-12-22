// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/ret_check_grpc.h"

#include <memory>
#include <string>

#include "absl/base/log_severity.h"
#include "absl/status/status.h"
#include "intrinsic/icon/release/source_location.h"
#include "intrinsic/util/status/status_builder_grpc.h"

namespace intrinsic {
namespace internal_status_macros_ret_check {

StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location) {
  return InternalErrorBuilderGrpc(location)
             .Log(absl::LogSeverity::kError)
             .EmitStackTrace()
         << "INTR_RET_CHECK failure (" << location.file_name() << ":"
         << location.line() << ") ";
}

StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           std::string* condition) {
  std::unique_ptr<std::string> cleanup(condition);
  return RetCheckFailSlowPathGrpc(location) << *condition << " ";
}

StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           const char* condition) {
  return RetCheckFailSlowPathGrpc(location) << condition << " ";
}

StatusBuilderGrpc RetCheckFailSlowPathGrpc(intrinsic::SourceLocation location,
                                           const char* condition,
                                           const absl::Status& status) {
  return RetCheckFailSlowPathGrpc(location)
         << condition << " returned " << status.ToString() << " ";
}

}  // namespace internal_status_macros_ret_check
}  // namespace intrinsic
