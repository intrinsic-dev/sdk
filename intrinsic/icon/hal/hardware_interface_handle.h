// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_

#include <sys/types.h>

#include <cstdint>
#include <utility>

#include "flatbuffers/flatbuffers.h"                 // IWYU pragma: keep
#include "intrinsic/icon/hal/icon_state_register.h"  // IWYU pragma: keep
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/current_cycle.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/icon/utils/realtime_status_or.h"

namespace intrinsic::icon {

// A read-only hardware interface handle to a shared memory segment.
// Throughout the lifetime of the hardware interface, we have to keep the shared
// memory segment alive. We therefore transparently wrap the hardware interface
// around the shared memory segment, exposing solely the actual hardware
// interface type.
// Prefer using a StrictHardwareInterfaceHandle for reading commands/status
// messages.
//
// Used internally by the StrictHardwareInterfaceHandle.
template <class T>
class HardwareInterfaceHandle {
 public:
  HardwareInterfaceHandle() = default;

  // Preferred constructor.
  explicit HardwareInterfaceHandle(ReadOnlyMemorySegment<T>&& segment)
      : segment_(std::forward<decltype(segment)>(segment)),
        hardware_interface_(flatbuffers::GetRoot<T>(segment_.GetRawValue())) {}
  const T* operator*() const { return hardware_interface_; }

  const T* operator->() const { return hardware_interface_; }

  // Returns the number of updates made to the segment. This helps detect issues
  // with missing updates.
  int64_t NumUpdates() const { return segment_.Header().NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() const { return segment_.Header().LastUpdatedTime(); }
  // Returns the cycle the segment was last updated. This helps detect stale
  // data.
  uint64_t LastUpdatedCycle() const {
    return segment_.Header().LastUpdatedCycle();
  }

 private:
  ReadOnlyMemorySegment<T> segment_;
  const T* hardware_interface_ = nullptr;
};

// A read-write hardware interface handle to a shared memory segment.
// Throughout the lifetime of the hardware interface, we have to keep the shared
// memory segment alive. We therefore transparently wrap the hardware interface
// around the shared memory segment, exposing solely the actual hardware
// interface type.
// Prefer using a MutableStrictHardwareInterfaceHandle for writing
// commands/status messages.
// Used internally by the MutableStrictHardwareInterfaceHandle.
template <class T>
class MutableHardwareInterfaceHandle {
 public:
  MutableHardwareInterfaceHandle() = default;

  // Preferred constructor.
  explicit MutableHardwareInterfaceHandle(ReadWriteMemorySegment<T>&& segment)
      : segment_(std::forward<decltype(segment)>(segment)),
        hardware_interface_(
            flatbuffers::GetMutableRoot<T>(segment_.GetRawValue())) {}

  T* operator*() { return hardware_interface_; }
  const T* operator*() const { return hardware_interface_; }

  T* operator->() { return hardware_interface_; }
  const T* operator->() const { return hardware_interface_; }

  // Returns the number of updates made to the segment. This helps detect issues
  // with missing updates.
  int64_t NumUpdates() const { return segment_.Header().NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() const { return segment_.Header().LastUpdatedTime(); }
  // Returns the cycle the segment was last updated. This helps detect stale
  // data.
  uint64_t LastUpdatedCycle() const {
    return segment_.Header().LastUpdatedCycle();
  }

  // Updates the `time` and current_cycle at which the segment was last updated
  // and increments an update counter.
  // The special IconState interface can be used to validate that the
  // interface was updated in the same cycle IconState reports as the current
  // cycle
  void UpdatedAt(Time time) {
    segment_.UpdatedAt(time, Cycle::GetCurrentCycle());
  }

 private:
  ReadWriteMemorySegment<T> segment_;
  T* hardware_interface_ = nullptr;
};

// Validates that the `hw_interface` was updated in the current control cycle.
// Returns FailedPreconditionError if not.
template <class HardwareInterfaceT>
inline RealtimeStatus WasUpdatedThisCycle(
    const HardwareInterfaceHandle<intrinsic_fbs::IconState>& icon_state,
    const HardwareInterfaceT& hw_interface) {
  if (icon_state.LastUpdatedCycle() != icon_state->current_cycle())
      [[unlikely]] {
    return icon::FailedPreconditionError(
        "Cycle count of ICON state is inconsistent.");
  }

  if (hw_interface.LastUpdatedCycle() != icon_state->current_cycle())
      [[unlikely]] {
    return icon::FailedPreconditionError(RealtimeStatus::StrCat(
        "Command was not updated this cycle. icon_cycle[",
        icon_state->current_cycle(), "] != command_cycle[",
        hw_interface.LastUpdatedCycle(), "]"));
  }
  return OkStatus();
}

// Wraps a a read-only hardware interface handle, and an IconState handle, and
// checks that `Value` was updated same cycle IconState reports as the current
// cycle.
// Use this interface to read commands/status messages.
template <class T>
class StrictHardwareInterfaceHandle {
 public:
  StrictHardwareInterfaceHandle() = default;

  // Preferred constructor.
  explicit StrictHardwareInterfaceHandle(
      HardwareInterfaceHandle<T> hardware_interface,
      HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state)
      : hardware_interface_(std::move(hardware_interface)),
        icon_state_(std::move(icon_state)) {}

  // Read only access to the stored value.
  // Checks that the value was updated same cycle IconState reports as the
  // current cycle.
  // Returns FailedPreconditionError when not.
  RealtimeStatusOr<const T*> Value() const {
    INTRINSIC_RT_RETURN_IF_ERROR(
        WasUpdatedThisCycle(icon_state_, hardware_interface_));
    return *hardware_interface_;
  }

  // Returns the number of updates made to the segment. This helps detect issues
  // with missing updates.
  int64_t NumUpdates() const { return hardware_interface_.NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() const { return hardware_interface_.LastUpdatedTime(); }
  // Returns the cycle the segment was last updated. This helps detect stale
  // data.
  uint64_t LastUpdatedCycle() const {
    return hardware_interface_.LastUpdatedCycle();
  }

 private:
  HardwareInterfaceHandle<T> hardware_interface_;
  HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state_;
};

// Wraps a a read-write hardware interface handle, and an IconState handle.
// Checks that `Value` was updated same cycle IconState reports as the current
// cycle.
// Use this interface to write commands/status messages.
// Also use this interface to read commands where you also have mutable access.
template <class T>
class MutableStrictHardwareInterfaceHandle {
 public:
  MutableStrictHardwareInterfaceHandle() = default;

  // Preferred constructor.
  explicit MutableStrictHardwareInterfaceHandle(
      MutableHardwareInterfaceHandle<T> hardware_interface,
      HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state)
      : hardware_interface_(std::move(hardware_interface)),
        icon_state_(std::move(icon_state)) {}

  // Mutable access to the stored value.
  // Does not check when the value was updated.
  // Call `UpdatedAt` once all values are written to update the cycle
  // information.
  T* MutableValue() { return *hardware_interface_; }

  // Read only access to the stored value.
  // Checks that the value was updated same cycle IconState reports as the
  // current cycle.
  // Returns FailedPreconditionError when not.
  RealtimeStatusOr<const T*> Value() const {
    INTRINSIC_RT_RETURN_IF_ERROR(
        WasUpdatedThisCycle(icon_state_, hardware_interface_));
    return *hardware_interface_;
  }

  // Returns the number of updates made to the segment. This helps detect issues
  // with missing updates.
  int64_t NumUpdates() const { return hardware_interface_.NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() const { return hardware_interface_.LastUpdatedTime(); }
  // Returns the cycle the segment was last updated. This helps detect stale
  // data.
  uint64_t LastUpdatedCycle() const {
    return hardware_interface_.LastUpdatedCycle();
  }

  // Updates the `time` and current_cycle at which the segment was last updated
  // and increments an update counter.
  void UpdatedAt(Time time) { hardware_interface_.UpdatedAt(time); }

 private:
  MutableHardwareInterfaceHandle<T> hardware_interface_;
  HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state_;
};
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_
