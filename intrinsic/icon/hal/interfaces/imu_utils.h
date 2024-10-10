// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_IMU_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_IMU_UTILS_H_

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffers.h"
#include "intrinsic/icon/hal/interfaces/imu.fbs.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildImuStatus();

}

#endif  // INTRINSIC_ICON_HAL_INTERFACES_IMU_UTILS_H_
