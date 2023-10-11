// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_

#include "intrinsic/icon/hal/interfaces/control_mode_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildControlModeStatus(ControlMode status);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_
