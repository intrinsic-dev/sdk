// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
#define INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_

#include <cstddef>
#include <string>

#include "absl/base/attributes.h"
#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "flatbuffers/detached_buffer.h"
#include "intrinsic/icon/hal/get_hardware_interface.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/testing/realtime_annotations.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

// Hardware Modules use the HardwareInterfaceRegistry to advertise their
// interfaces.
//
// See the documentation on the various Advertise functions for details, and
// note in particular the distinction between strict and non-strict interfaces.
class HardwareInterfaceRegistry {
 public:
  HardwareInterfaceRegistry() = delete;
  ~HardwareInterfaceRegistry() = default;

  // This class is move-only.
  HardwareInterfaceRegistry(const HardwareInterfaceRegistry& other) = delete;
  HardwareInterfaceRegistry& operator=(const HardwareInterfaceRegistry& other) =
      delete;
  HardwareInterfaceRegistry(HardwareInterfaceRegistry&& other) = default;
  HardwareInterfaceRegistry& operator=(HardwareInterfaceRegistry&& other) =
      default;

  // Constructs a new registry for hardware interfaces.
  // `shared_memory_manager` must outlive the return value of this function.
  explicit HardwareInterfaceRegistry(
      SharedMemoryManager& shared_memory_manager ABSL_ATTRIBUTE_LIFETIME_BOUND);

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
    return icon::GetInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
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
    return icon::GetMutableInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
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
    return icon::GetMutableInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
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
    return icon::GetStrictInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
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
    return icon::GetMutableStrictInterfaceHandle<HardwareInterfaceT>(
        *shm_manager_, interface_name);
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
    return icon::GetMutableStrictInterfaceHandle<HardwareInterfaceT>(
        *shm_manager_, interface_name);
  }

  // Convenience function that returns a handle to a registered interface.
  template <class HardwareInterfaceT>
  absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
  GetInterfaceHandle(absl::string_view interface_name) const {
    return icon::GetInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
                                                        interface_name);
  }

  // Convenience function that returns a mutable handle to a registered
  // interface.
  template <class HardwareInterfaceT>
  absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
  GetMutableInterfaceHandle(absl::string_view interface_name) const {
    return icon::GetMutableInterfaceHandle<HardwareInterfaceT>(*shm_manager_,
                                                               interface_name);
  }

  // Returns the number of registered interfaces.
  size_t Size() const {
    return shm_manager_->GetRegisteredMemoryNames().size();
  }

  // Name of the module owning this registry.
  std::string ModuleName() const INTRINSIC_NON_REALTIME_ONLY {
    return shm_manager_->ModuleName();
  }

  // Namespace for the shared memory interfaces using this registry.
  std::string SharedMemoryNamespace() const INTRINSIC_NON_REALTIME_ONLY {
    return shm_manager_->SharedMemoryNamespace();
  }

 private:
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

  SharedMemoryManager* shm_manager_;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_HAL_HARDWARE_INTERFACE_REGISTRY_H_
