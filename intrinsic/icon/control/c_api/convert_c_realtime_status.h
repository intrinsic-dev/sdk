// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_REALTIME_STATUS_H_
#define INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_REALTIME_STATUS_H_

#include "absl/status/status.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// These helpers convert back and forth between ICON/Abseil C++ Status values
// types and their C API equivalent.
//
// A static_assert in convert_c_types.cc ensures that the maximum length for
// messages in both C and C++ RealtimeStatus is the same.

// Truncates the message in `status` to at most
// kXfaIconRealtimeStatusMaxMessageLength characters.
XfaIconRealtimeStatus FromAbslStatus(const absl::Status& status);

absl::Status ToAbslStatus(const XfaIconRealtimeStatus& status);

XfaIconRealtimeStatus FromRealtimeStatus(const RealtimeStatus& status);

RealtimeStatus ToRealtimeStatus(const XfaIconRealtimeStatus& status);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_CONVERT_C_REALTIME_STATUS_H_
