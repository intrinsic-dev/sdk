// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/realtime_clock_interface.h"

namespace intrinsic::icon {

RealtimeStatus RealtimeClockInterface::TickBlockingWithTimeout(
    intrinsic::Time current_timestamp, absl::Duration timeout) {
  return TickBlockingWithDeadline(current_timestamp, absl::Now() + timeout);
}

}  // namespace intrinsic::icon
