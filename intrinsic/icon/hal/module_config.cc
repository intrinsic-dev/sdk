// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/module_config.h"

#include <string>

#include "intrinsic/icon/hardware_modules/sim_bus/sim_bus_hardware_module.pb.h"

namespace intrinsic::icon {
namespace internal {

bool RegisterProtoTypes(absl::string_view type) {
  GetRegisteredConfigProtoTypes().emplace(type);
  return true;
}

}  // namespace internal

ModuleConfig::ModuleConfig(
    const intrinsic_proto::icon::HardwareModuleConfig& config,
    RealtimeClockInterface* realtime_clock,
    const Thread::Options& icon_thread_options)
    : config_(config),
      realtime_clock_(realtime_clock),
      icon_thread_options_(icon_thread_options) {}

intrinsic_proto::icon::SimBusModuleConfig ModuleConfig::GetSimulationConfig()
    const {
  return config_.simulation_module_config();
}

const std::string& ModuleConfig::GetName() const { return config_.name(); }

Thread::Options ModuleConfig::GetIconThreadOptions() const {
  return icon_thread_options_;
}

RealtimeClockInterface* ModuleConfig::GetRealtimeClock() const {
  return realtime_clock_;
}

absl::flat_hash_set<std::string>& GetRegisteredConfigProtoTypes() {
  static auto* proto_types = new absl::flat_hash_set<std::string>();
  return *proto_types;
}

absl::string_view ModuleConfig::GetSimulationServerAddress() const {
  return config_.simulation_server_address();
}

}  // namespace intrinsic::icon
