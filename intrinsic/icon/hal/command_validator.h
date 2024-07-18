// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_COMMAND_VALIDATOR_H_
#define INTRINSIC_ICON_HAL_COMMAND_VALIDATOR_H_

#include <utility>

#include "absl/status/statusor.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_registry.h"
#include "intrinsic/icon/hal/icon_state_register.h"  // IWYU pragma: keep
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {

// Validates that a command interface was updated in the current control cycle
// by checking the `LastUpdateCycle` value of the interface against the
// `current_cycle()` count reported by the `IconState` interface.
class Validator {
 public:
  // Prefer `Create`, a default constructed Validator will not work!
  // Default constructor so Validator can be used in containers/StatusOr.
  Validator() = default;

  // Creates a Validator that checks the 'freshness' of hardware interface
  // commands. Forwards errors from opening the `IconState` interface.
  static absl::StatusOr<Validator> Create(
      HardwareInterfaceRegistry& interface_registry);

  // Validates that `hw_interface` was updated in the current control cycle.
  // Returns FailedPreconditionError if not.
  // The recommended type for `HardwareInterfaceT` is
  // HardwareInterfaceHandle<T>.
  // * MutableHardwareInterfaceHandle<T> should not
  //   require validation, because it is for writing.
  // * StrictHardwareInterfaceHandle<T> already validates the command when
  //   accessing the data.
  template <class HardwareInterfaceT>
  RealtimeStatus WasUpdatedThisCycle(HardwareInterfaceT& hw_interface) const {
    if (*icon_state_ == nullptr) [[unlikely]] {
      return icon::InternalError(
          RealtimeStatus::StrCat("Using a default constructed Validator is not "
                                 "supported. Use 'Create' instead."));
    }

    if (icon_state_.LastUpdatedCycle() != icon_state_->current_cycle())
        [[unlikely]] {
      return icon::InternalError(RealtimeStatus::StrCat(
          "ICON cycle was never updated. This likely means that "
          "HardwareModuleProxy::ApplyCommand was never called and should only "
          "be possible in tests."));
    }

    if (hw_interface.LastUpdatedCycle() != icon_state_->current_cycle())
        [[unlikely]] {
      return icon::FailedPreconditionError(RealtimeStatus::StrCat(
          "ICON did not provide a command this cycle. icon_cycle[",
          (*icon_state_)->current_cycle(), "] != command_cycle[",
          hw_interface.LastUpdatedCycle(), "]"));
    }
    return OkStatus();
  }

 private:
  // Constructs a Validator that checks the 'freshness' of hardware interface
  // commands.
  explicit Validator(
      HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state)
      : icon_state_(std::move(icon_state)) {};

  HardwareInterfaceHandle<intrinsic_fbs::IconState> icon_state_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_COMMAND_VALIDATOR_H_
