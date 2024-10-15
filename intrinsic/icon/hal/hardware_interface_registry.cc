// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/hardware_interface_registry.h"

#include <stdint.h>

#include <cstring>
#include <string>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

HardwareInterfaceRegistry::HardwareInterfaceRegistry(
    SharedMemoryManager& shared_memory_manager)
    : shm_manager_(&shared_memory_manager) {}

absl::Status HardwareInterfaceRegistry::AdvertiseInterfaceT(
    absl::string_view interface_name, bool must_be_used,
    const flatbuffers::DetachedBuffer& buffer, absl::string_view type_id) {
  // Create a shared memory segment that is big enough to hold the SegmentHeader
  // and the flatbuffer payload.
  INTR_RETURN_IF_ERROR(shm_manager_->AddSegment(
      interface_name, must_be_used, buffer.size(), std::string(type_id)));
  uint8_t* const shm_data = shm_manager_->GetRawValue(interface_name);
  std::memcpy(shm_data, buffer.data(), buffer.size());

  return absl::OkStatus();
}
}  // namespace intrinsic::icon
