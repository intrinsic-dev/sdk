// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CC_CLIENT_OPERATIONAL_STATUS_H_
#define INTRINSIC_ICON_CC_CLIENT_OPERATIONAL_STATUS_H_

#include <iostream>
#include <ostream>
#include <string>

#include "absl/base/attributes.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic::icon {

// Types representing the operational status of the server.
//
// Use `Client::Enable()`, `Client::Disable()`,
// `Client::ClearFaults()` and `Client::GetOperationalStatus()` to get
// and set the operational state. See client.h for details.

// Enum of possible operational states of the server.
enum class OperationalState {
  // Indicates that server is not ready for sessions to start.
  // `icon_client.Enable()` must be called first.
  kDisabled,

  // Indicates that a part (or the server as a whole) is in an erroneous state.
  // `icon_client.ClearFaults()` must be called to return the system to a
  // disabled state before attempting other operations.
  kFaulted,

  // Indicates that the server is ready for a session to begin.
  kEnabled
};

// Describes the operational status of the server, which includes the
// operational state along with additional details when the server is kFaulted.
class OperationalStatus final {
 public:
  // Constructs an OperationalStatus with state set to `kDisabled`
  OperationalStatus();

  // Creates an `OperationalStatus` object with state set to `kDisabled`.
  static OperationalStatus Disabled();
  // Creates an `OperationalStatus` object with state set to `kFaulted`.
  // `reason` is a human-readable description of what caused the fault.
  static OperationalStatus Faulted(absl::string_view reason);
  // Creates an `OperationalStatus` object with state set to `kEnabled`.
  static OperationalStatus Enabled();

  // Returns the operational state.
  OperationalState state() const { return state_; }

  // Returns a human-readable description of what caused the `kFaulted` state.
  // When not in the `kFaulted` state, returns an empty string.
  std::string fault_reason() const { return fault_reason_; }

 private:
  // Private constructor. Use static methods (`Disabled()`, etc.) to create an
  // `OperationalStatus` object.
  OperationalStatus(OperationalState state, absl::string_view fault_reason);

  OperationalState state_;
  std::string fault_reason_;
};

// These convenience functions return `true` if a given status matches the
// OperationalState of its associated function.
ABSL_MUST_USE_RESULT bool IsDisabled(const OperationalStatus& status);
ABSL_MUST_USE_RESULT bool IsFaulted(const OperationalStatus& status);
ABSL_MUST_USE_RESULT bool IsEnabled(const OperationalStatus& status);

// Converts an OperationalState to a string. For example,
// `ToString(OperationalState::kDisabled)` returns `"DISABLED"`.
std::string ToString(OperationalState state);

// Converts an OpertationalStatus to a string.
// If `IsDisabled(status)` returns `"DISABLED"`.
// If `IsFaulted(status)` returns `"FAULTED(reason)"` where `reason` is
// `status.fault_reason()`.
// If `IsEnabled(status)` returns `"ENABLED"`.
std::string ToString(const OperationalStatus& status);

// operator<<
//
// Prints a human-readable representation of `state` to `os`.
std::ostream& operator<<(std::ostream& os, OperationalState state);

// operator<<
//
// Prints a human-readable representation of `status` to `os`.
std::ostream& operator<<(std::ostream& os, const OperationalStatus& status);

// These functions convert the types declared in this header to/from proto.
intrinsic_proto::icon::OperationalState ToProto(OperationalState state);
intrinsic_proto::icon::OperationalStatus ToProto(
    const OperationalStatus& status);
absl::StatusOr<OperationalState> FromProto(
    const intrinsic_proto::icon::OperationalState& proto);
absl::StatusOr<OperationalStatus> FromProto(
    const intrinsic_proto::icon::OperationalStatus& proto);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CC_CLIENT_OPERATIONAL_STATUS_H_
