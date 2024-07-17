// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_INTERFACES_JOINT_STATE_UTILS_H_
#define INTRINSIC_ICON_HAL_INTERFACES_JOINT_STATE_UTILS_H_

#include <cstdint>

#include "flatbuffers/detached_buffer.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildJointPositionState(uint32_t num_dof);

flatbuffers::DetachedBuffer BuildJointVelocityState(uint32_t num_dof);

flatbuffers::DetachedBuffer BuildJointAccelerationState(uint32_t num_dof);

flatbuffers::DetachedBuffer BuildJointTorqueState(uint32_t num_dof);

}  // namespace intrinsic_fbs

#endif  // INTRINSIC_ICON_HAL_INTERFACES_JOINT_STATE_UTILS_H_
