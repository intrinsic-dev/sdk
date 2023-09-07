// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/hardware_interface_registry.h"

#include <stdint.h>

#include <cstring>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_generated.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic::icon {

absl::StatusOr<HardwareInterfaceRegistry> HardwareInterfaceRegistry::Create(
    const ModuleConfig& module_config) {
  if (module_config.GetName().empty()) {
    return absl::InvalidArgumentError(
        "No name specified in hardware module config.");
  }
  return HardwareInterfaceRegistry(module_config);
}

HardwareInterfaceRegistry::HardwareInterfaceRegistry(
    const ModuleConfig& module_config)
    : module_config_(module_config) {}

absl::Status HardwareInterfaceRegistry::AdvertiseInterfaceT(
    absl::string_view interface_name, const flatbuffers::DetachedBuffer& buffer,
    absl::string_view type_id) {
  std::string shm_name =
      GetHardwareInterfaceID(module_config_.GetName(), interface_name);
  INTRINSIC_RETURN_IF_ERROR(
      shm_manager_.AddSegment(shm_name, buffer.size(), std::string(type_id)));

  uint8_t* const shm_data = shm_manager_.GetRawValue(shm_name);
  std::memcpy(shm_data, buffer.data(), buffer.size());

  return absl::OkStatus();
}

absl::Status HardwareInterfaceRegistry::AdvertiseHardwareInfo() {
  std::string shm_name = GetHardwareModuleID(module_config_.GetName());

  auto segment_info = shm_manager_.GetSegmentInfo();
  INTRINSIC_RETURN_IF_ERROR(shm_manager_.AddSegment<SegmentInfo>(
      shm_name, segment_info, hal::kModuleInfoName));

  return absl::OkStatus();
}

}  // namespace intrinsic::icon
