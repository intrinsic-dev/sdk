// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_UTILS_CURRENT_CYCLE_H_
#define INTRINSIC_ICON_UTILS_CURRENT_CYCLE_H_

#include <atomic>
#include <cstdint>
#include <limits>

namespace intrinsic::icon {

// Singleton.
// Allows accessing the CurrentCycle without passing references trough the ICON
// stack.
//
// It is assumed that there is one main control loop in charge of updating the
// current cycle.
// And any number of readers using `GetCurrentCycle`.
// The value of current cycle is not guaranteed to be static or continuous.
// It can overflow, or jump (if SetCurrentCycle is called).
//
// Expected Usage:
// * During Init: (optionally) Initial value is set using `SetCurrentCycle`.
// * During realtime operation:
//   * In the main control loop call `IncrementCurrentCycle()`.
//   * Use `GetCurrentCycle()` to get the current cycle where required.
class Cycle final {
 public:
  Cycle() = delete;
  Cycle(Cycle &other) = delete;
  void operator=(const Cycle &) = delete;

  // Thread safe. Returns the current cycle.
  static uint64_t GetCurrentCycle() noexcept { return current_cycle_; }

  // Adjusts the value of current cycle.
  // Not thread safe. Calling SetCurrentCycle in parallel to
  // IncrementCurrentCycle will result in either of the updates getting lost.
  // Calling SetCurrentCycle in parallel can result in updates getting lost.
  static void SetCurrentCycle(uint64_t cycle) noexcept {
    current_cycle_ = cycle;
  }

  // Increments the value of current cycle while handling overruns.
  // Not thread safe. Calling SetCurrentCycle in parallel to
  // IncrementCurrentCycle will result in either of the updates getting lost.
  // Calling IncrementCurrentCycle in parallel can result in updates getting
  // lost.
  static void IncrementCurrentCycle() noexcept {
    // Uses copy of current cycle in case `SetCurrentCycle` is called while
    // `IncrementCurrentCycle` is active.
    // The value set by `SetCurrentCycle` will be lost in that case.
    uint64_t current_cycle = current_cycle_;
    // Explicitly handle overruns, because the behavior is compiler specific.
    if (current_cycle == std::numeric_limits<uint64_t>::max()) [[unlikely]] {
      current_cycle = std::numeric_limits<uint64_t>::min();
    } else {
      ++current_cycle;
    }
    current_cycle_ = current_cycle;
  }

 private:
  inline static std::atomic_uint64_t current_cycle_ = 0;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_UTILS_CURRENT_CYCLE_H_
