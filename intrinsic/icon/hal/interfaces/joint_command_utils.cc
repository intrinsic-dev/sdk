// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/joint_command_utils.h"

#include <cstdint>
#include <vector>

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/joint_command.fbs.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildJointPositionCommand(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_pos = builder.CreateVector(zeros);
  auto default_ff_vel = builder.CreateVector(zeros);
  auto default_ff_acc = builder.CreateVector(zeros);
  auto position_command = CreateJointPositionCommand(
      builder, default_pos, default_ff_vel, default_ff_acc);
  builder.Finish(position_command);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildJointVelocityCommand(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_vel = builder.CreateVector(zeros);
  auto default_ff_acc = builder.CreateVector(zeros);
  auto velocity_command =
      CreateJointVelocityCommand(builder, default_vel, default_ff_acc);
  builder.Finish(velocity_command);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildJointTorqueCommand(uint32_t num_dof) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  std::vector<double> zeros(num_dof, 0.0);
  auto default_torque = builder.CreateVector(zeros);
  auto torque_command = CreateJointTorqueCommand(builder, default_torque);
  builder.Finish(torque_command);
  return builder.Release();
}

flatbuffers::DetachedBuffer BuildHandGuidingCommand() {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  builder.Finish(builder.CreateStruct(HandGuidingCommand(/*unused=*/false)));
  return builder.Release();
}
}  // namespace intrinsic_fbs
