// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_

#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/interfaces/control_mode.fbs.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildControlModeStatus(ControlMode status);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_CONTROL_MODE_UTILS_H_
