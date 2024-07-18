// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/robot_controller_utils.h"

#include <cmath>

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/robot_controller.fbs.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildRobotControllerStatus() {
  flatbuffers::FlatBufferBuilder builder;
  builder.Finish(builder.CreateStruct(
      RobotControllerStatus(/*speed_scaling=*/std::nan("1"))));
  return builder.Release();
}

}  // namespace intrinsic_fbs
