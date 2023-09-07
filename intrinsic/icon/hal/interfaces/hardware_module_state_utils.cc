// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/interfaces/hardware_module_state_utils.h"

#include <cstring>
#include <string_view>

#include "flatbuffers/detached_buffer.h"
#include "flatbuffers/flatbuffer_builder.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"

namespace intrinsic_fbs {

flatbuffers::DetachedBuffer BuildHardwareModuleState() {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);

  builder.Finish(builder.CreateStruct(HardwareModuleState()));
  return builder.Release();
}

void SetState(HardwareModuleState* hardware_module_state, StateCode code,
              std::string_view message) {
  size_t max_length = hardware_module_state->message()->size();
  max_length = message.size() < max_length ? message.size() : max_length;
  hardware_module_state->mutate_code(code);
  std::memcpy(hardware_module_state->mutable_message()->Data(), message.data(),
              max_length);
  hardware_module_state->mutable_message()->Data()[max_length] = '\0';
}

std::string_view GetMessage(const HardwareModuleState* hardware_module_state) {
  return reinterpret_cast<const char*>(
      hardware_module_state->message()->Data());
}
}  // namespace intrinsic_fbs
