// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_

#include <memory>
#include <utility>

#include "flatbuffers/flatbuffers.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/utils/clock.h"

namespace intrinsic::icon {

// A read-only hardware interface handle to a shared memory segment.
// Throughout the lifetime of the hardware interface, we have to keep the shared
// memory segment alive. We therefore transparently wrap the hardware interface
// around the shared memory segment, exposing solely the actual hardware
// interface type.
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
  int64_t NumUpdates() { return segment_.Header().NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() { return segment_.Header().LastUpdatedTime(); }

 private:
  ReadOnlyMemorySegment<T> segment_;
  const T* hardware_interface_ = nullptr;
};

// A read-write hardware interface handle to a shared memory segment.
// Throughout the lifetime of the hardware interface, we have to keep the shared
// memory segment alive. We therefore transparently wrap the hardware interface
// around the shared memory segment, exposing solely the actual hardware
// interface type.
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
  int64_t NumUpdates() { return segment_.Header().NumUpdates(); }
  // Returns the time the segment was last updated. This helps detect stale
  // data.
  Time LastUpdatedTime() { return segment_.Header().LastUpdatedTime(); }

  // Updates the time at which the segment was last updated and increments an
  // update counter.
  void UpdatedAt(Time time) { segment_.UpdatedAt(time); }

 private:
  ReadWriteMemorySegment<T> segment_;
  T* hardware_interface_ = nullptr;
};
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_HANDLE_H_
