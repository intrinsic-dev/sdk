// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/interfaces/payload_command_utils.h"

#include "flatbuffers/buffer.h"
#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/payload_command.fbs.h"
#include "intrinsic/icon/hal/interfaces/robot_payload.fbs.h"
#include "intrinsic/icon/hal/interfaces/robot_payload_utils.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildPayloadCommand() {
  flatbuffers::FlatBufferBuilder fbb;
  fbb.ForceDefaults(true);

  flatbuffers::Offset<OptionalRobotPayload> payload =
      AddOptionalRobotPayload(fbb);

  PayloadCommandBuilder builder(fbb);
  builder.add_full_payload(payload);

  auto payload_command = builder.Finish();

  fbb.Finish(payload_command);
  return fbb.Release();
}

}  // namespace intrinsic_fbs
