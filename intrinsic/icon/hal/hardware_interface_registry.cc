// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/hardware_interface_registry.h"

#include <stdint.h>

#include <cstring>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

HardwareInterfaceRegistry::HardwareInterfaceRegistry(
    absl::string_view memory_namespace) {
  module_config_ = ModuleConfig(intrinsic_proto::icon::HardwareModuleConfig{},
                                memory_namespace, /*realtime_clock*/ nullptr);
}

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
    absl::string_view interface_name, bool must_be_used,
    const flatbuffers::DetachedBuffer& buffer, absl::string_view type_id) {
  MemoryName shm_name =
      GetHardwareInterfaceID(module_config_.GetSharedMemoryNamespace(),
                             module_config_.GetName(), interface_name);
  INTR_RETURN_IF_ERROR(shm_manager_.AddSegment(
      shm_name, must_be_used, buffer.size(), std::string(type_id)));

  uint8_t* const shm_data = shm_manager_.GetRawValue(shm_name);
  std::memcpy(shm_data, buffer.data(), buffer.size());

  return absl::OkStatus();
}

absl::Status HardwareInterfaceRegistry::AdvertiseHardwareInfo() {
  MemoryName shm_name = GetHardwareModuleID(
      module_config_.GetSharedMemoryNamespace(), module_config_.GetName());

  auto segment_info = shm_manager_.GetSegmentInfo();
  INTR_RETURN_IF_ERROR(shm_manager_.AddSegment<SegmentInfo>(
      shm_name, /**must_be_used=*/false, segment_info, hal::kModuleInfoName));

  return absl::OkStatus();
}

}  // namespace intrinsic::icon
