// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_

#include <string_view>

#include "flatbuffers/flatbuffers.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildHardwareModuleState();

void SetState(HardwareModuleState* hardware_module_state, StateCode code,
              std::string_view message);

std::string_view GetMessage(const HardwareModuleState* hardware_module_state);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_HARDWARE_MODULE_STATE_UTILS_H_
