// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_REALTIME_CLOCK_INTERFACE_H_
#define INTRINSIC_ICON_CONTROL_REALTIME_CLOCK_INTERFACE_H_

#include "absl/time/time.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// RealtimeClockInterface is an abstract interface for advancing ICON's control
// loop.
class RealtimeClockInterface {
 public:
  // Steps ICON's real time update loop, blocking the current thread until it
  // has finished or the deadline has expired.
  //
  // The update loop includes the following steps:
  //
  // 1) Sets `current_timestamp` as the canonical time for control purposes
  // during the tick of the update loop;
  // 2) Calls `ReadStatus` for all hardware modules;
  // 3) Calls `Sense` for all active actions;
  // 4) Calls `Control` for all active actions;
  // 5) Handles reactions (updating next cycle's active actions);
  // 6) Calls `ApplyCommand` for all hardware modules.
  //
  // This may be called from any thread, but is not re-entrant.
  //
  // An error may indicate that one of the above steps failed, OR it may
  // indicate that communication with the control layer has failed.
  virtual RealtimeStatus TickBlockingWithDeadline(
      intrinsic::Time current_timestamp, absl::Time deadline) = 0;

  // Same as TickBlockingWithDeadline but with a timeout instead of a deadline.
  RealtimeStatus TickBlockingWithTimeout(intrinsic::Time current_timestamp,
                                         absl::Duration timeout);

  // Resets the clock in order to recover after a failure during
  // `TickBlockingWithTimeout`. Leaves the clock in a state, ready to start
  // `TickBlockingWithTimeout`.
  virtual RealtimeStatus Reset(absl::Duration timeout) = 0;

  virtual ~RealtimeClockInterface() = default;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_REALTIME_CLOCK_INTERFACE_H_
