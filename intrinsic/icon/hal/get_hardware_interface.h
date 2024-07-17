// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_
#define INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_

#include <string>
#include <utility>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_split.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/icon_state_register.h"  // IWYU pragma: keep
#include "intrinsic/icon/hal/interfaces/icon_state_generated.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_generated.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_utils.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

namespace hal {
static constexpr char kModuleInfoName[] = "intrinsic_module_info";
}  // namespace hal

// Constructs the SHM location identifier for a hardware interface.
inline MemoryName GetHardwareInterfaceID(absl::string_view memory_namespace,
                                         absl::string_view module_name,
                                         absl::string_view interface_name) {
  return MemoryName(memory_namespace, module_name, interface_name);
}

// Constructs the SHM location identifier for the hardware module info.
inline MemoryName GetHardwareModuleID(absl::string_view memory_namespace,
                                      absl::string_view module_name) {
  return MemoryName(memory_namespace, module_name, hal::kModuleInfoName);
}

// Returns a handle to a registered interface.
template <class HardwareInterfaceT>
inline absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
GetInterfaceHandle(absl::string_view memory_namespace,
                   absl::string_view module_name,
                   absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto ro_segment,
      ReadOnlyMemorySegment<HardwareInterfaceT>::Get(GetHardwareInterfaceID(
          memory_namespace, module_name, interface_name)));
  if (ro_segment.Header().Type().TypeID() !=
      hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Type mismatch: Interface '", interface_name,
        "' was requested with type '",
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString,
        "' but has type '", ro_segment.Header().Type().TypeID(), "'"));
  }

  return HardwareInterfaceHandle<HardwareInterfaceT>(std::move(ro_segment));
}

// Returns a mutable handle to a registered interface.
template <class HardwareInterfaceT>
inline absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
GetMutableInterfaceHandle(absl::string_view memory_namespace,
                          absl::string_view module_name,
                          absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto rw_segment,
      ReadWriteMemorySegment<HardwareInterfaceT>::Get(GetHardwareInterfaceID(
          memory_namespace, module_name, interface_name)));
  if (rw_segment.Header().Type().TypeID() !=
      hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Type mismatch: Interface '", interface_name,
        "' was requested with type '",
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString,
        "' but has type '", rw_segment.Header().Type().TypeID(), "'"));
  }

  return MutableHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(rw_segment));
}

// Returns a handle to a HardwareInterfaceT that checks that it was
// updated in the same ICON cycle as the "icon_state" interface.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<StrictHardwareInterfaceHandle<HardwareInterfaceT>>
GetStrictInterfaceHandle(absl::string_view memory_namespace,
                         absl::string_view module_name,
                         absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(auto handle,
                        GetInterfaceHandle<HardwareInterfaceT>(
                            memory_namespace, module_name, interface_name));

  INTR_ASSIGN_OR_RETURN(
      auto icon_state,
      GetInterfaceHandle<intrinsic_fbs::IconState>(
          memory_namespace, module_name, kIconStateInterfaceName));

  return StrictHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(handle), std::move(icon_state));
}

// Returns a mutable handle to a HardwareInterfaceT that checks that it was
// updated in the same ICON cycle as the "icon_state" interface.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>>
GetMutableStrictInterfaceHandle(absl::string_view memory_namespace,
                                absl::string_view module_name,
                                absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(auto handle,
                        GetMutableInterfaceHandle<HardwareInterfaceT>(
                            memory_namespace, module_name, interface_name));

  INTR_ASSIGN_OR_RETURN(
      auto icon_state,
      GetInterfaceHandle<intrinsic_fbs::IconState>(
          memory_namespace, module_name, kIconStateInterfaceName));

  return MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(handle), std::move(icon_state));
}

// Returns information about the exported interfaces from a hardware module.
inline absl::StatusOr<ReadOnlyMemorySegment<SegmentInfo>> GetHardwareModuleInfo(
    absl::string_view memory_namespace, absl::string_view module_name) {
  return ReadOnlyMemorySegment<SegmentInfo>::Get(
      GetHardwareModuleID(memory_namespace, module_name));
}

// Extracts the names of the shared memory segments.
// A typical shared memory location is represented in the style of
// `/some_prefix__some_name`. This function will truncate the segment location
// and only return the name suffix of it.
//
// If the location identifier does not conform to the above mentioned style, the
// complete location will be returned.
inline absl::StatusOr<std::vector<std::string>> GetInterfacesFromModuleInfo(
    const SegmentInfo& segment_info) {
  std::vector<std::string> names = GetNamesFromSegmentInfo(segment_info);
  // A typical shared memory location looks like `/some_module__some_interface`.
  // We split it by `__` and take the latter part.
  for (auto& name : names) {
    std::vector<absl::string_view> split_location = absl::StrSplit(name, "__");
    if (split_location.size() != 2) {
      return absl::InternalError(absl::StrCat(
          "Exported shared memory location '", name,
          "' does not adhere to norm of '/<module_name>__<segment_name>'"));
    }
    name = split_location[1];
  }
  return names;
}

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_
