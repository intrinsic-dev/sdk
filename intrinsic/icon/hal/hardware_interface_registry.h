// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/release/status_helpers.h"

namespace intrinsic::icon {

class HardwareInterfaceRegistry {
 public:
  HardwareInterfaceRegistry() = default;

  // Creates a new registry for hardware interfaces.
  // Fails if the module config doesn't contain all necessary details, such as
  // the module name.
  static absl::StatusOr<HardwareInterfaceRegistry> Create(
      const ModuleConfig& module_config);

  // Advertises a new hardware interface given an interface type and a set of
  // arguments used to initialize this interface.
  // The arguments are according to the respective `Builder` function as
  // specified via a call to the `INTRINSIC_ADD_HARDWARE_INTERFACE` macro, c.f.
  // `intrinsic/icon/hal/hardware_interface_traits.h`.
  // The interface is allocated within a shared memory segment.
  // Returns a non-mutable handle to the newly allocated hardware interface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseInterface(absl::string_view interface_name, ArgsT... args) {
    INTRINSIC_RETURN_IF_ERROR(
        AdvertiseInterfaceT<HardwareInterfaceT>(interface_name, args...));
    return GetInterfaceHandle<HardwareInterfaceT>(module_config_.GetName(),
                                                  interface_name);
  }

  // Advertises a new mutable hardware interface.
  // This functions behaves exactly like `AdvertiseInterface` except that it
  // returns a handle to mutable interface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableInterface(absl::string_view interface_name, ArgsT... args) {
    INTRINSIC_RETURN_IF_ERROR(
        AdvertiseInterfaceT<HardwareInterfaceT>(interface_name, args...));
    return GetMutableInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetName(), interface_name);
  }

  template <class HardwareInterfaceT>
  absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableInterface(absl::string_view interface_name,
                            flatbuffers::DetachedBuffer&& message_buffer) {
    auto type_id =
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString;
    INTRINSIC_RETURN_IF_ERROR(
        AdvertiseInterfaceT(interface_name, message_buffer, type_id));
    return GetMutableInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetName(), interface_name);
  }

  // Writes the currently advertised and registered interfaces in a module
  // specific location in shared memory.
  // This function is usually called once after the initialization is done so
  // that other processes can dynamically lookup interfaces from this module.
  absl::Status AdvertiseHardwareInfo();

  // Returns the number of registered interfaces.
  size_t Size() const {
    return shm_manager_.GetRegisteredSegmentNames().size();
  }

 private:
  explicit HardwareInterfaceRegistry(const ModuleConfig& module_config);

  template <class HardwareInterfaceT, typename... ArgsT>
  absl::Status AdvertiseInterfaceT(absl::string_view interface_name,
                                   ArgsT... args) {
    static_assert(
        hardware_interface_traits::BuilderFunctions<HardwareInterfaceT>::value,
        "No builder function defined.");
    flatbuffers::DetachedBuffer buffer =
        hardware_interface_traits::BuilderFunctions<HardwareInterfaceT>::kBuild(
            args...);
    auto type_id =
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString;
    return AdvertiseInterfaceT(interface_name, buffer, type_id);
  }

  absl::Status AdvertiseInterfaceT(absl::string_view interface_name,
                                   const flatbuffers::DetachedBuffer& buffer,
                                   absl::string_view type_id);

  ModuleConfig module_config_;
  intrinsic::icon::SharedMemoryManager shm_manager_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
