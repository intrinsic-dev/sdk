// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_ICON_STATE_REGISTER_H_
#define INTRINSIC_ICON_HAL_ICON_STATE_REGISTER_H_

#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/icon/hal/interfaces/icon_state_utils.h"

namespace intrinsic::icon {

// Reserved name of the ICON state interface.
static constexpr absl::string_view kIconStateInterfaceName = "icon_state";

namespace hardware_interface_traits {

// Registers the IconState hardware interface.
// Allows transparently depending on IconState and can be included in multiple
// files.
//
// Usage:
// #include "intrinsic/icon/hal/icon_state_register.h"  // IWYU pragma: keep
INTRINSIC_ADD_HARDWARE_INTERFACE(intrinsic_fbs::IconState,
                                 intrinsic_fbs::BuildIconState,
                                 "intrinsic_fbs.IconState")
}  // namespace hardware_interface_traits
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_ICON_STATE_REGISTER_H_
