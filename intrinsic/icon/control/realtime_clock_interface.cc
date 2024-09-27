// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/realtime_clock_interface.h"

#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

RealtimeStatus RealtimeClockInterface::TickBlockingWithTimeout(
    intrinsic::Time current_timestamp, absl::Duration timeout) {
  return TickBlockingWithDeadline(current_timestamp, absl::Now() + timeout);
}

}  // namespace intrinsic::icon
