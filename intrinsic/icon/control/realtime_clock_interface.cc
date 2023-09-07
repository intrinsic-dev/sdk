// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/realtime_clock_interface.h"

namespace intrinsic::icon {

RealtimeStatus RealtimeClockInterface::TickBlockingWithTimeout(
    intrinsic::Time current_timestamp, absl::Duration timeout) {
  return TickBlockingWithDeadline(current_timestamp, absl::Now() + timeout);
}

}  // namespace intrinsic::icon
