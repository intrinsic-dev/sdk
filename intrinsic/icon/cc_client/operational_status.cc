// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/cc_client/operational_status.h"

#include <ostream>
#include <string>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/proto/types.pb.h"

namespace intrinsic::icon {

OperationalStatus::OperationalStatus() : state_(OperationalState::kDisabled) {}

OperationalStatus::OperationalStatus(OperationalState state,
                                     absl::string_view fault_reason)
    : state_(state), fault_reason_(fault_reason) {
  // This CHECK should never be reached because OperationalStatus can only be
  // constructed via the public factories (Disabled(), etc.).
  CHECK(fault_reason.empty() || state == OperationalState::kFaulted)
      << "fault_reason should be empty for states other than "
         "OperationalState::kFaulted";
}

// static
OperationalStatus OperationalStatus::Disabled() {
  return OperationalStatus(OperationalState::kDisabled, "");
}

// static
OperationalStatus OperationalStatus::Enabled() {
  return OperationalStatus(OperationalState::kEnabled, "");
}

// static
OperationalStatus OperationalStatus::Faulted(absl::string_view reason) {
  return OperationalStatus(OperationalState::kFaulted, reason);
}

bool IsDisabled(const OperationalStatus& status) {
  return status.state() == OperationalState::kDisabled;
}

bool IsEnabled(const OperationalStatus& status) {
  return status.state() == OperationalState::kEnabled;
}

bool IsFaulted(const OperationalStatus& status) {
  return status.state() == OperationalState::kFaulted;
}

std::string ToString(OperationalState state) {
  return intrinsic_proto::icon::OperationalState_Name(ToProto(state));
}

std::string ToString(const OperationalStatus& status) {
  if (IsFaulted(status)) {
    return absl::StrCat("FAULTED(", status.fault_reason(), ")");
  }
  return ToString(status.state());
}

std::ostream& operator<<(std::ostream& os, OperationalState state) {
  return os << ToString(state);
}

std::ostream& operator<<(std::ostream& os, const OperationalStatus& status) {
  return os << ToString(status);
}

intrinsic_proto::icon::OperationalState ToProto(OperationalState state) {
  switch (state) {
    case OperationalState::kDisabled:
      return intrinsic_proto::icon::OperationalState::DISABLED;
    case OperationalState::kFaulted:
      return intrinsic_proto::icon::OperationalState::FAULTED;
    case OperationalState::kEnabled:
      return intrinsic_proto::icon::OperationalState::ENABLED;
  }
  return intrinsic_proto::icon::OperationalState::UNKNOWN;
}

intrinsic_proto::icon::OperationalStatus ToProto(
    const OperationalStatus& status) {
  intrinsic_proto::icon::OperationalStatus out;
  out.set_state(ToProto(status.state()));
  out.set_fault_reason(status.fault_reason());
  return out;
}

absl::StatusOr<OperationalState> FromProto(
    const intrinsic_proto::icon::OperationalState& proto) {
  switch (proto) {
    case intrinsic_proto::icon::OperationalState::DISABLED:
      return OperationalState::kDisabled;
    case intrinsic_proto::icon::OperationalState::FAULTED:
      return OperationalState::kFaulted;
    case intrinsic_proto::icon::OperationalState::ENABLED:
      return OperationalState::kEnabled;
    default:
      return absl::InvalidArgumentError(absl::StrCat(
          "Unexpected value in proto::OperationalState: proto=", proto));
  }
}

absl::StatusOr<OperationalStatus> FromProto(
    const intrinsic_proto::icon::OperationalStatus& proto) {
  if (!proto.fault_reason().empty() &&
      proto.state() != intrinsic_proto::icon::OperationalState::FAULTED) {
    return absl::InvalidArgumentError(
        absl::StrCat("Invalid proto::OperationalStatus: fault_reason is "
                     "non-empty but state is not FAULTED: proto=",
                     proto));
  }
  switch (proto.state()) {
    case intrinsic_proto::icon::OperationalState::DISABLED:
      return OperationalStatus::Disabled();
    case intrinsic_proto::icon::OperationalState::FAULTED:
      return OperationalStatus::Faulted(proto.fault_reason());
    case intrinsic_proto::icon::OperationalState::ENABLED:
      return OperationalStatus::Enabled();
    default:
      return absl::InvalidArgumentError(absl::StrCat(
          "Unexpected state value in proto::OperationalStatus: proto=", proto));
  }
}

}  // namespace intrinsic::icon
