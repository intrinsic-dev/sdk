// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_

#include <string_view>

#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildHardwareModuleState();

void SetState(HardwareModuleState* hardware_module_state, StateCode code,
              std::string_view message);

// Returns the message associated with the given state.
//
// Returns an empty string if `hardware_module_state` or
// `hardware_module_state->message()` is null.
std::string_view GetMessage(const HardwareModuleState* hardware_module_state);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_
