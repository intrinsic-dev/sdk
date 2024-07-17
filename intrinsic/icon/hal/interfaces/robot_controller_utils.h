// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_ROBOT_CONTROLLER_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_ROBOT_CONTROLLER_UTILS_H_

#include "flatbuffers/detached_buffer.h"

namespace intrinsic_fbs {

// Builds a ControllerStatus with speed_scaling initialized to NaN.
flatbuffers::DetachedBuffer BuildRobotControllerStatus();

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_ROBOT_CONTROLLER_UTILS_H_
