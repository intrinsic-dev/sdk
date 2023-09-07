// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_HARDWARE_MODULE_REGISTRY_H_
#define INTRINSIC_ICON_HAL_HARDWARE_MODULE_REGISTRY_H_

#include <memory>

#include "intrinsic/icon/hal/hardware_module_interface.h"
#include "intrinsic/icon/hal/proto/hardware_module_config.pb.h"

// `CreateInstance` is defined here and implemented below through a call to
// `REGISTER_HARDWARE_MODULE`.
// If we try to link a module implementation without a call to the macro, the
// linker complains about an undefined reference. Similarly, if we try to link
// two module implementations into the same binary, we get a duplicate symbol
// error.
// Note, we deliberately don't use any of the existing function/class registry
// implementations in //util due to its dependency overhead. Additionally, we
// enforce a strong 1:1 relationship between the main binary
// (`hardware_module_main.cc`) and a registered module. Therefore, we don't need
// any ref-counted instance creation, nor a name-lookup of multiple classes to
// be instantiated. If a second module is getting linked to the main binary,
// we'd get a symbol collision during linking time.
namespace intrinsic::icon {
namespace hardware_module_registry {

intrinsic::icon::HardwareModule CreateInstance(
    const ModuleConfig& config,
    std::unique_ptr<RealtimeClockInterface> realtime_clock);

}  // namespace hardware_module_registry
}  // namespace intrinsic::icon

#define REGISTER_HARDWARE_MODULE(HARDWARE_MODULE)                   \
  namespace intrinsic::icon::hardware_module_registry {             \
  HardwareModule CreateInstance(                                    \
      const ModuleConfig& config,                                   \
      std::unique_ptr<RealtimeClockInterface> realtime_clock) {     \
    HardwareModule hardware_module;                                 \
    hardware_module.config = config;                                \
    hardware_module.instance = std::make_unique<HARDWARE_MODULE>(); \
    hardware_module.realtime_clock = std::move(realtime_clock);     \
    return hardware_module;                                         \
  }                                                                 \
  }  // namespace intrinsic::icon::hardware_module_registry

#endif  // INTRINSIC_ICON_HAL_HARDWARE_MODULE_REGISTRY_H_
