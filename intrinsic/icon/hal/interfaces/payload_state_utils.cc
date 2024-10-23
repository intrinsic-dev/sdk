// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/payload_state_utils.h"

#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/payload_state.fbs.h"
#include "intrinsic/icon/hal/interfaces/robot_payload.fbs.h"
#include "intrinsic/icon/hal/interfaces/robot_payload_utils.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildPayloadState() {
  flatbuffers::FlatBufferBuilder fbb;
  fbb.ForceDefaults(true);

  flatbuffers::Offset<OptionalRobotPayload> payload =
      AddOptionalRobotPayload(fbb);

  PayloadStateBuilder builder(fbb);
  builder.add_full_payload(payload);

  auto payload_state = builder.Finish();

  fbb.Finish(payload_state);
  return fbb.Release();
}

}  // namespace intrinsic_fbs
