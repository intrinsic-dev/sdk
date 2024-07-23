// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_

#include <cstddef>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/module_config.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

class HardwareInterfaceRegistry {
 public:
  HardwareInterfaceRegistry() = default;
  explicit HardwareInterfaceRegistry(absl::string_view memory_namespace);

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
  // Prefer AdvertiseStrictInterface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseInterface(absl::string_view interface_name, ArgsT... args) {
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT<HardwareInterfaceT>(
        interface_name, /*must_be_used=*/false, args...));
    return GetInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  // Advertises a new mutable hardware interface.
  // This functions behaves exactly like `AdvertiseInterface` except that it
  // returns a handle to mutable interface.
  // Prefer AdvertiseStrictInterface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableInterface(absl::string_view interface_name, ArgsT... args) {
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT<HardwareInterfaceT>(
        interface_name, /*must_be_used=*/false, args...));
    return GetMutableInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  // Prefer AdvertiseMutableStrictInterface.
  template <class HardwareInterfaceT>
  absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableInterface(absl::string_view interface_name,
                            flatbuffers::DetachedBuffer&& message_buffer) {
    auto type_id =
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString;
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT(
        interface_name, /*must_be_used=*/false, message_buffer, type_id));
    return GetMutableInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  // Advertises a new strict hardware interface using the interface type and a
  // set of arguments used to initialize this interface.
  //
  // A strict interface checks that it was updated in the same cycle the special
  // IconState interface reports as the current cycle when reading its data.
  //
  // Marks the hardware interface as required, which tells ICON that the
  // interface needs to be used in the ICON configuration.
  //
  // The arguments are according to the respective `Builder` function as
  // specified via a call to the `INTRINSIC_ADD_HARDWARE_INTERFACE` macro, c.f.
  // `intrinsic/icon/hal/hardware_interface_traits.h`.
  // The interface is allocated within a shared memory segment.
  // Returns a non-mutable handle to the newly allocated hardware interface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<StrictHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseStrictInterface(absl::string_view interface_name, ArgsT... args) {
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT<HardwareInterfaceT>(
        interface_name, /*must_be_used=*/true, args...));
    return GetStrictInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  // Advertises a new mutable strict hardware interface using the interface type
  // and a set of arguments used to initialize this interface.
  //
  // A strict interface checks that it was updated in the same cycle the special
  // IconState interface reports as the current cycle when reading its data.
  //
  // Marks the hardware interface as required, which tells ICON that the
  // interface needs to be used in the ICON configuration.
  //
  // The arguments are according to the respective `Builder` function as
  // specified via a call to the `INTRINSIC_ADD_HARDWARE_INTERFACE` macro, c.f.
  // `intrinsic/icon/hal/hardware_interface_traits.h`.
  // The interface is allocated within a shared memory segment.
  // Returns a mutable handle to the newly allocated hardware interface.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::StatusOr<MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableStrictInterface(absl::string_view interface_name,
                                  ArgsT... args) {
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT<HardwareInterfaceT>(
        interface_name, /*must_be_used=*/true, args...));
    return GetMutableStrictInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  template <class HardwareInterfaceT>
  absl::StatusOr<MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>>
  AdvertiseMutableStrictInterface(
      absl::string_view interface_name,
      flatbuffers::DetachedBuffer&& message_buffer) {
    auto type_id =
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString;
    INTR_RETURN_IF_ERROR(AdvertiseInterfaceT(
        interface_name, /*must_be_used=*/true, message_buffer, type_id));
    return GetMutableStrictInterfaceHandle<HardwareInterfaceT>(
        module_config_.GetSharedMemoryNamespace(), module_config_.GetName(),
        interface_name);
  }

  // Writes the currently advertised and registered interfaces in a module
  // specific location in shared memory.
  // This function is usually called once after the initialization is done so
  // that other processes can dynamically lookup interfaces from this module.
  absl::Status AdvertiseHardwareInfo();

  // Returns the number of registered interfaces.
  size_t Size() const { return shm_manager_.GetRegisteredMemoryNames().size(); }

  // Name of the module owning this registry.
  std::string ModuleName() const INTRINSIC_NON_REALTIME_ONLY {
    return module_config_.GetName();
  }

  // Namespace for the shared memory interfaces using this registry.
  std::string SharedMemoryNamespace() const INTRINSIC_NON_REALTIME_ONLY {
    return std::string(module_config_.GetSharedMemoryNamespace());
  }

 private:
  explicit HardwareInterfaceRegistry(const ModuleConfig& module_config);

  // The parameter `must_be_used` tells ICON that this interface needs to be
  // used in its configuration.
  template <class HardwareInterfaceT, typename... ArgsT>
  absl::Status AdvertiseInterfaceT(absl::string_view interface_name,
                                   bool must_be_used, ArgsT... args) {
    static_assert(
        hardware_interface_traits::BuilderFunctions<HardwareInterfaceT>::value,
        "No builder function defined.");
    flatbuffers::DetachedBuffer buffer =
        hardware_interface_traits::BuilderFunctions<HardwareInterfaceT>::kBuild(
            args...);
    auto type_id =
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString;
    return AdvertiseInterfaceT(interface_name, must_be_used, buffer, type_id);
  }

  // The parameter `must_be_used` tells ICON that this interface needs to be
  // used in its configuration.
  absl::Status AdvertiseInterfaceT(absl::string_view interface_name,
                                   bool must_be_used,
                                   const flatbuffers::DetachedBuffer& buffer,
                                   absl::string_view type_id);

  ModuleConfig module_config_;
  intrinsic::icon::SharedMemoryManager shm_manager_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
