// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/interfaces/joint_state_utils.h"

#include <vector>

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildJointPositionState(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_pos = builder.CreateVector(zeros);
  auto position_state = CreateJointPositionState(builder, default_pos);
  builder.Finish(position_state);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildJointVelocityState(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_vel = builder.CreateVector(zeros);
  auto velocity_state = CreateJointVelocityState(builder, default_vel);
  builder.Finish(velocity_state);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildJointAccelerationState(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_acc = builder.CreateVector(zeros);
  auto acceleration_state = CreateJointAccelerationState(builder, default_acc);
  builder.Finish(acceleration_state);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildJointTorqueState(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_torque = builder.CreateVector(zeros);
  auto torque_state = CreateJointTorqueState(builder, default_torque);
  builder.Finish(torque_state);
  return builder.Release();
}

}  // namespace intrinsic_fbs
