// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/utils/realtime_status.h"

#include <algorithm>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/utils/fixed_str_cat.h"

namespace intrinsic {
namespace icon {

// static char arrays for error messages.

namespace {
class RealtimeStatusCodeCharArray {
 public:
  static constexpr char kOk[] = "OK";
  static constexpr char kCancelled[] = "CANCELLED";
  static constexpr char kUnknown[] = "UNKNOWN";
  static constexpr char kInvalidArgument[] = "INVALID_ARGUMENT";
  static constexpr char kDeadlineExceeded[] = "DEADLINE_EXCEEDED";
  static constexpr char kNotFound[] = "NOT_FOUND";
  static constexpr char kAlreadyExists[] = "ALREADY_EXISTS";
  static constexpr char kPermissionDenied[] = "PERMISSION_DENIED";
  static constexpr char kResourceExhausted[] = "RESOURCE_EXHAUSTED";
  static constexpr char kFailedPrecondition[] = "FAILED_PRECONDITION";
  static constexpr char kAborted[] = "ABORTED";
  static constexpr char kOutOfRange[] = "OUT_OF_RANGE";
  static constexpr char kUnimplemented[] = "UNIMPLEMENTED";
  static constexpr char kInternal[] = "INTERNAL";
  static constexpr char kUnavailable[] = "UNAVAILABLE";
  static constexpr char kDataLoss[] = "DATA_LOSS";
  static constexpr char kUnauthenticated[] = "UNAUTHENTICATED";
  static constexpr char kDefault[] = "";
};
}  // namespace

RealtimeStatus::operator absl::Status() const {
  INTRINSIC_ASSERT_NON_REALTIME();
  return {code_, message_};
}

// Handles the mapping between Enum and char[]
absl::string_view RealtimeStatusCodeToCharArray(absl::StatusCode code) {
  switch (code) {
    case absl::StatusCode::kOk:
      return RealtimeStatusCodeCharArray::kOk;
    case absl::StatusCode::kCancelled:
      return RealtimeStatusCodeCharArray::kCancelled;
    case absl::StatusCode::kUnknown:
      return RealtimeStatusCodeCharArray::kUnknown;
    case absl::StatusCode::kInvalidArgument:
      return RealtimeStatusCodeCharArray::kInvalidArgument;
    case absl::StatusCode::kDeadlineExceeded:
      return RealtimeStatusCodeCharArray::kDeadlineExceeded;
    case absl::StatusCode::kNotFound:
      return RealtimeStatusCodeCharArray::kNotFound;
    case absl::StatusCode::kAlreadyExists:
      return RealtimeStatusCodeCharArray::kAlreadyExists;
    case absl::StatusCode::kPermissionDenied:
      return RealtimeStatusCodeCharArray::kPermissionDenied;
    case absl::StatusCode::kUnauthenticated:
      return RealtimeStatusCodeCharArray::kUnauthenticated;
    case absl::StatusCode::kResourceExhausted:
      return RealtimeStatusCodeCharArray::kResourceExhausted;
    case absl::StatusCode::kFailedPrecondition:
      return RealtimeStatusCodeCharArray::kFailedPrecondition;
    case absl::StatusCode::kAborted:
      return RealtimeStatusCodeCharArray::kAborted;
    case absl::StatusCode::kOutOfRange:
      return RealtimeStatusCodeCharArray::kOutOfRange;
    case absl::StatusCode::kUnimplemented:
      return RealtimeStatusCodeCharArray::kUnimplemented;
    case absl::StatusCode::kInternal:
      return RealtimeStatusCodeCharArray::kInternal;
    case absl::StatusCode::kUnavailable:
      return RealtimeStatusCodeCharArray::kUnavailable;
    case absl::StatusCode::kDataLoss:
      return RealtimeStatusCodeCharArray::kDataLoss;
    default:
      return RealtimeStatusCodeCharArray::kDefault;
  }
}

RealtimeStatus::RealtimeStatus() : code_(absl::StatusCode::kOk) {}

RealtimeStatus::RealtimeStatus(absl::StatusCode code, absl::string_view message)
    : code_(code), message_(message) {}

RealtimeStatus AbortedError(absl::string_view message) {
  return {absl::StatusCode::kAborted, message};
}

RealtimeStatus AlreadyExistsError(absl::string_view message) {
  return {absl::StatusCode::kAlreadyExists, message};
}

RealtimeStatus CancelledError(absl::string_view message) {
  return {absl::StatusCode::kCancelled, message};
}

RealtimeStatus DataLossError(absl::string_view message) {
  return {absl::StatusCode::kDataLoss, message};
}

RealtimeStatus DeadlineExceededError(absl::string_view message) {
  return {absl::StatusCode::kDeadlineExceeded, message};
}

RealtimeStatus FailedPreconditionError(absl::string_view message) {
  return {absl::StatusCode::kFailedPrecondition, message};
}

RealtimeStatus InternalError(absl::string_view message) {
  return {absl::StatusCode::kInternal, message};
}

RealtimeStatus InvalidArgumentError(absl::string_view message) {
  return {absl::StatusCode::kInvalidArgument, message};
}

RealtimeStatus NotFoundError(absl::string_view message) {
  return {absl::StatusCode::kNotFound, message};
}

RealtimeStatus OutOfRangeError(absl::string_view message) {
  return {absl::StatusCode::kOutOfRange, message};
}

RealtimeStatus PermissionDeniedError(absl::string_view message) {
  return {absl::StatusCode::kPermissionDenied, message};
}

RealtimeStatus ResourceExhaustedError(absl::string_view message) {
  return {absl::StatusCode::kResourceExhausted, message};
}

RealtimeStatus UnauthenticatedError(absl::string_view message) {
  return {absl::StatusCode::kUnauthenticated, message};
}

RealtimeStatus UnavailableError(absl::string_view message) {
  return {absl::StatusCode::kUnavailable, message};
}

RealtimeStatus UnimplementedError(absl::string_view message) {
  return {absl::StatusCode::kUnimplemented, message};
}

RealtimeStatus UnknownError(absl::string_view message) {
  return {absl::StatusCode::kUnknown, message};
}

RealtimeStatus OkStatus() { return {}; }

bool IsAborted(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kAborted;
}

bool IsAlreadyExists(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kAlreadyExists;
}

bool IsCancelled(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kCancelled;
}

bool IsDataLoss(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kDataLoss;
}

bool IsDeadlineExceeded(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kDeadlineExceeded;
}

bool IsFailedPrecondition(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kFailedPrecondition;
}

bool IsInternal(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kInternal;
}

bool IsInvalidArgument(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kInvalidArgument;
}

bool IsNotFound(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kNotFound;
}

bool IsOutOfRange(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kOutOfRange;
}

bool IsPermissionDenied(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kPermissionDenied;
}

bool IsResourceExhausted(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kResourceExhausted;
}

bool IsUnauthenticated(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kUnauthenticated;
}

bool IsUnavailable(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kUnavailable;
}

bool IsUnimplemented(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kUnimplemented;
}

bool IsUnknown(const RealtimeStatus& status) {
  return status.code() == absl::StatusCode::kUnknown;
}

}  // namespace icon

}  // namespace intrinsic
