// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/interfaces/control_mode_utils.h"

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/control_mode_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildControlModeStatus(ControlMode status) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  auto control_mode_status = CreateControlModeStatus(builder, status);
  builder.Finish(control_mode_status);
  return builder.Release();
}

}  // namespace intrinsic_fbs
