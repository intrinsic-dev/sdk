// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_REALTIME_CLOCK_H_
#define INTRINSIC_ICON_HAL_REALTIME_CLOCK_H_

#include <stdint.h>

#include <memory>
#include <string>
#include <string_view>

#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/control/realtime_clock_interface.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/interprocess/shared_memory_lockstep/shared_memory_lockstep.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Payload for clock updates; gets stored in shared memory.
struct RealtimeClockUpdate {
  // Cycle start time in nanoseconds since the epoch.
  int64_t cycle_start_nanoseconds;
};

// RealtimeClock is an implementation of RealtimeClockInterface used by
// hardware modules to drive the realtime clock. It talks with the ICON server
// over shared memory.
class RealtimeClock : public RealtimeClockInterface {
 public:
  // Creates a RealtimeClock for `hardware_module_name`. This creates memory
  // segments named `LockstepSegmentName(hardware_module_name)` and
  // `RealtimeClockStepSegmentName(hardware_module_name)`.
  static absl::StatusOr<std::unique_ptr<RealtimeClock>> Create(
      absl::string_view hardware_module_name);

  // This class is non-moveable and non-copyable to ensure that custom
  // destructor logic only ever runs once.
  RealtimeClock(const RealtimeClock& other) = delete;
  RealtimeClock& operator=(const RealtimeClock& other) = delete;

  // Signals to the ICON server that a real time cycle should begin. Blocks
  // until the cycle's update logic has completed; that is, blocks until
  // ApplyCommand has completed for all hardware modules. It is the caller's
  // responsibility to further wait until the next cycle's start time before
  // calling this again.
  //
  // The current_timestamp is considered the start time for the cycle.
  // Returns a deadline exceeded error in case of the deadline has expired.
  // Don't assume that the realtime cycle has been completed in case of such an
  // error. Use `Reset` to recover from such a situation!
  RealtimeStatus TickBlockingWithDeadline(intrinsic::Time current_timestamp,
                                          absl::Time deadline) override;

  // Resets the clock to its state after initialization, i.e. ready to call
  // TickBlockingWithTimeout.
  // Returns a deadline exceeded error on timeout.
  RealtimeStatus Reset(absl::Duration timeout) override;

  ~RealtimeClock() override;

 private:
  // The provided `lockstep` object synchronizes the callsite with the ICON
  // server's realtime update loop. The provided `realtime_clock_update`
  // communicates the cycle start time.
  RealtimeClock(
      SharedMemoryLockstep lockstep,
      ReadWriteMemorySegment<RealtimeClockUpdate> realtime_clock_update,
      SharedMemoryManager shm_manager);

  SharedMemoryLockstep lockstep_;
  ReadWriteMemorySegment<RealtimeClockUpdate> update_;
  SharedMemoryManager shm_manager_;
};

// Returns the canonical name for a shared memory lockstep segment, based on a
// hardware module name.
inline std::string LockstepSegmentName(std::string_view hardware_module_name) {
  return absl::StrCat("/", hardware_module_name, hal::kDelimiter,
                      "realtime_clock_lockstep");
}

// Returns the canonical name for a RealtimeClockUpdate shared memory segment,
// based on a hardware module name.
inline std::string RealtimeClockUpdateSegmentName(
    std::string_view hardware_module_name) {
  return absl::StrCat("/", hardware_module_name, hal::kDelimiter,
                      "realtime_clock_update");
}

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_REALTIME_CLOCK_H_
