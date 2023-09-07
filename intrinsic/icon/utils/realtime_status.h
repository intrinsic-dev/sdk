// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_UTILS_REALTIME_STATUS_H_
#define INTRINSIC_ICON_UTILS_REALTIME_STATUS_H_

#include <cstddef>
#include <ostream>

#include "absl/base/attributes.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/icon/utils/fixed_str_cat.h"
#include "intrinsic/icon/utils/fixed_string.h"
#include "intrinsic/icon/utils/realtime_guard.h"

// Realtime safe Status implementation.
//
// Intended to be used for applications reporting Statuses from a realtime
// context.
//
// Supports all absl::StatusCodes found in
// "third_party/absl/status/status.h"
namespace intrinsic {
namespace icon {
// Handles the mapping between Enum and char[]
absl::string_view RealtimeStatusCodeToCharArray(absl::StatusCode code);

// A RealtimeStatus is a real-time safe version of absl::Status, with a maximum
// message length. RealtimeStatus is implicitly convertible to absl::Status.
class ABSL_MUST_USE_RESULT RealtimeStatus final {
 public:
  // Char array for error message.
  static constexpr size_t kMaxMessageLength = 100;

  // Local name for the FixedStrCat function that includes the correct maximum
  // message size.
  //
  // NOTE: This, like FixedStrCat, truncates messages to kMaxMessageLength. It
  // is your responsibility to make sure your error messages are not too long!
  template <typename... AV>
  static ABSL_MUST_USE_RESULT FixedString<kMaxMessageLength> StrCat(
      const AV&... args) {
    return FixedStrCat<kMaxMessageLength>(args...);
  }

  operator absl::Status() const;  // NOLINT: implicit conversion ok

  // Creates an ok status with no message or payload.
  RealtimeStatus() INTRINSIC_CHECK_REALTIME_SAFE;
  // Creates a RealtimeStatus with the specified code and error message.
  // If code == RealtimeStatusCode::kOk, message is ignored and an object
  // identical to an OK status is constructed. If message.length() is >
  // kMaxMessageLength, message is truncated.
  RealtimeStatus(absl::StatusCode code,
                 absl::string_view message) INTRINSIC_CHECK_REALTIME_SAFE;
  RealtimeStatus(const RealtimeStatus& status) = default;

  ~RealtimeStatus() = default;

  // Returns true if the Status is OK.
  ABSL_MUST_USE_RESULT bool ok() const INTRINSIC_CHECK_REALTIME_SAFE {
    return code_ == absl::StatusCode::kOk;
  }
  // Returns the (canonical) error code.
  absl::StatusCode code() const INTRINSIC_CHECK_REALTIME_SAFE { return code_; }

  // Returns the error message.
  // This message rarely describes the error code.  It is not unusual for the
  // error message to be the empty string.
  absl::string_view message() const ABSL_ATTRIBUTE_LIFETIME_BOUND
      INTRINSIC_CHECK_REALTIME_SAFE {
    return message_;
  }

  absl::string_view ToString() const ABSL_ATTRIBUTE_LIFETIME_BOUND
      INTRINSIC_CHECK_REALTIME_SAFE {
    return message_;
  }

  friend bool operator==(const RealtimeStatus& lhs, const RealtimeStatus& rhs)
      INTRINSIC_CHECK_REALTIME_SAFE;
  friend bool operator!=(const RealtimeStatus& lhs, const RealtimeStatus& rhs)
      INTRINSIC_CHECK_REALTIME_SAFE;

 private:
  // Error code.
  absl::StatusCode code_ = absl::StatusCode::kOk;
  FixedString<kMaxMessageLength> message_;
};

// Each of the functions below creates a RealtimeStatus object with a particular
// error code and the given message. The error code of the returned status
// object matches the name of the function.
RealtimeStatus AbortedError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus AlreadyExistsError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus CancelledError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus DataLossError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus DeadlineExceededError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus FailedPreconditionError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus InternalError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus InvalidArgumentError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus NotFoundError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus OutOfRangeError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus PermissionDeniedError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus ResourceExhaustedError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus UnauthenticatedError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus UnavailableError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus UnimplementedError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;
RealtimeStatus UnknownError(absl::string_view message)
    INTRINSIC_CHECK_REALTIME_SAFE;

// This function creates a RealtimeStatus object with status code
// RealtimeStatusCode::kOk, along with an empty message. Messages are ignored
// for Ok statuses. This method is functionally equivalent to the empty
// constructor, but is likely more readable in certain cases.
RealtimeStatus OkStatus() INTRINSIC_CHECK_REALTIME_SAFE;

// Each of the functions below returns true if the given status matches the
// error code implied by the function's name.
ABSL_MUST_USE_RESULT bool IsAborted(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsAlreadyExists(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsCancelled(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsDataLoss(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsDeadlineExceeded(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsFailedPrecondition(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsInternal(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsInvalidArgument(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsNotFound(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsOutOfRange(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsPermissionDenied(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsResourceExhausted(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsUnauthenticated(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsUnavailable(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsUnimplemented(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;
ABSL_MUST_USE_RESULT bool IsUnknown(const RealtimeStatus& status)
    INTRINSIC_CHECK_REALTIME_SAFE;

inline bool operator==(const RealtimeStatus& lhs, const RealtimeStatus& rhs) {
  if (lhs.code() != rhs.code()) {
    return false;
  }
  if (lhs.message_ != rhs.message_) {
    return false;
  }
  return true;
}

inline bool operator!=(const RealtimeStatus& lhs, const RealtimeStatus& rhs) {
  return !(lhs == rhs);
}

// Logging operator exposed for CHECK_* functions. These should only be called
// in non realtime contexts.
inline std::ostream& operator<<(std::ostream& os,
                                const RealtimeStatus& status) {
  INTRINSIC_ASSERT_NON_REALTIME();
  if (status.ok() || status.message().empty()) {
    return os << RealtimeStatusCodeToCharArray(status.code());
  }

  return os << RealtimeStatusCodeToCharArray(status.code()) << ": "
            << status.message();
}

// Returns `new_status` if it is non-OK, `previous_status` otherwise.
//
// Example (Foo() will return the last non-Ok status returned by Bar1(), Bar2()
// or Bar3()):
//
//    RealtimeStatus Bar1();
//    RealtimeStatus Bar2();
//    RealtimeStatus Bar3();
//
//    RealtimeStatus Foo() {
//      RealtimeStatus status = Bar1();
//      status = OverwriteIfError(status, Bar2());
//      status = OverwriteIfError(status, Bar3());
//      return status;
//    }
inline RealtimeStatus OverwriteIfError(const RealtimeStatus& previous_status,
                                       const RealtimeStatus& new_status) {
  if (!new_status.ok()) return new_status;
  return previous_status;
}

// Returns `new_status` if it is non-OK, `previous_status` otherwise.
//
// Example (Foo() will return the last non-Ok status returned by Bar1(), Bar2()
// or Bar3()):
//
//    absl::Status Bar1();
//    absl::Status Bar2();
//    absl::Status Bar3();
//
//    absl::Status Foo() {
//      absl::Status status = Bar1();
//      status = OverwriteIfError(status, Bar2());
//      status = OverwriteIfError(status, Bar3());
//      return status;
//    }
inline absl::Status OverwriteIfError(const absl::Status& previous_status,
                                     const absl::Status& new_status) {
  if (!new_status.ok()) return new_status;
  return previous_status;
}

// Returns `new_status` if `previous_status` is OK.
// Used to capture the first non-OK status in a list of sequential calls.
//
// Example (Foo() will return the first non-OK status returned by Bar1(), Bar2()
// or Bar3()):
//    RealtimeStatus Bar1();
//    RealtimeStatus Bar2();
//    RealtimeStatus Bar3();
//
//    RealtimeStatus Foo() {
//      RealtimeStatus status = Bar1();
//      status = OverwriteIfNotInError(status, Bar2());
//      status = OverwriteIfNotInError(status, Bar3());
//      return status;
//    }
inline RealtimeStatus OverwriteIfNotInError(
    const RealtimeStatus& previous_status, const RealtimeStatus& new_status) {
  if (previous_status.ok()) {
    return new_status;
  } else {
    return previous_status;
  }
}

// Returns `new_status` if `previous_status` is OK.
// Used to capture the first non-OK status in a list of sequential calls.
//
// Example (Foo() will return the first non-OK status returned by Bar1(), Bar2()
// or Bar3()):
//    absl::Status Bar1();
//    absl::Status Bar2();
//    absl::Status Bar3();
//
//    absl::Status Foo() {
//      absl::Status status = Bar1();
//      status = OverwriteIfNotInError(status, Bar2());
//      status = OverwriteIfNotInError(status, Bar3());
//      return status;
//    }
inline absl::Status OverwriteIfNotInError(const absl::Status& previous_status,
                                          const absl::Status& new_status) {
  if (previous_status.ok()) {
    return new_status;
  } else {
    return previous_status;
  }
}

}  // namespace icon
}  // namespace intrinsic

#endif  // INTRINSIC_ICON_UTILS_REALTIME_STATUS_H_
