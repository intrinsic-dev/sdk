// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_
#define INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_

#include <string>
#include <utility>
#include <vector>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/hal/hardware_interface_handle.h"
#include "intrinsic/icon/hal/hardware_interface_traits.h"
#include "intrinsic/icon/hal/icon_state_register.h"  // IWYU pragma: keep
#include "intrinsic/icon/hal/interfaces/icon_state.fbs.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_header.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info.fbs.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/segment_info_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon {

namespace hal {
static constexpr char kModuleInfoName[] = "intrinsic_module_info";
}  // namespace hal

// Returns an error if the type or version of the segment header doesn't match
// SegmentHeader::ExpectedVersion().
// The parameter `interface_name` is used for error reporting.
template <class HardwareInterfaceT>
absl::Status SegmentHeaderIsValid(const SegmentHeader& segment_header,
                                  absl::string_view interface_name) {
  if (segment_header.Version() != SegmentHeader::ExpectedVersion()) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Version mismatch: Interface '", interface_name, "' has version '",
        segment_header.Version(), "' but expected version '",
        SegmentHeader::ExpectedVersion(), "'"));
  }

  if (segment_header.Type().TypeID() !=
      hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Type mismatch: Interface '", interface_name, "' has type '",
        segment_header.Type().TypeID(), "' but expected type '",
        hardware_interface_traits::TypeID<HardwareInterfaceT>::kTypeString,
        "'"));
  }
  return absl::OkStatus();
}

// Returns a handle to a HardwareInterfaceT.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
GetInterfaceHandle(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
    absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto ro_segment,
      ReadOnlyMemorySegment<HardwareInterfaceT>::Get(
          segment_name_to_file_descriptor_map, interface_name));

  INTR_RETURN_IF_ERROR(SegmentHeaderIsValid<HardwareInterfaceT>(
      ro_segment.Header(), interface_name));

  return HardwareInterfaceHandle<HardwareInterfaceT>(std::move(ro_segment));
}

// Returns a mutable handle to a HardwareInterfaceT.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
GetMutableInterfaceHandle(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
    absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto rw_segment,
      ReadWriteMemorySegment<HardwareInterfaceT>::Get(
          segment_name_to_file_descriptor_map, interface_name));

  INTR_RETURN_IF_ERROR(SegmentHeaderIsValid<HardwareInterfaceT>(
      rw_segment.Header(), interface_name));

  return MutableHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(rw_segment));
}

// Returns a handle to a HardwareInterfaceT.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<HardwareInterfaceHandle<HardwareInterfaceT>>
GetInterfaceHandle(const SharedMemoryManager& shared_memory_manager,
                   absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto ro_segment,
      shared_memory_manager.Get<ReadOnlyMemorySegment<HardwareInterfaceT>>(
          interface_name));

  INTR_RETURN_IF_ERROR(SegmentHeaderIsValid<HardwareInterfaceT>(
      ro_segment.Header(), interface_name));

  return HardwareInterfaceHandle<HardwareInterfaceT>(std::move(ro_segment));
}

// Returns a mutable handle to a HardwareInterfaceT.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<MutableHardwareInterfaceHandle<HardwareInterfaceT>>
GetMutableInterfaceHandle(const SharedMemoryManager& shared_memory_manager,
                          absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto rw_segment,
      shared_memory_manager.Get<ReadWriteMemorySegment<HardwareInterfaceT>>(
          interface_name));

  INTR_RETURN_IF_ERROR(SegmentHeaderIsValid<HardwareInterfaceT>(
      rw_segment.Header(), interface_name));

  return MutableHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(rw_segment));
}

// Returns a handle to a HardwareInterfaceT that checks that it was
// updated in the same ICON cycle as the "icon_state" interface.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<StrictHardwareInterfaceHandle<HardwareInterfaceT>>
GetStrictInterfaceHandle(const SharedMemoryManager& shared_memory_manager,
                         absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(
      auto handle, GetInterfaceHandle<HardwareInterfaceT>(shared_memory_manager,
                                                          interface_name));

  INTR_ASSIGN_OR_RETURN(auto icon_state,
                        GetInterfaceHandle<intrinsic_fbs::IconState>(
                            shared_memory_manager, kIconStateInterfaceName));

  return StrictHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(handle), std::move(icon_state));
}

// Returns a mutable handle to a HardwareInterfaceT that checks that it was
// updated in the same ICON cycle as the "icon_state" interface.
// The HardwareInterfaceT must be registered with the
// INTRINSIC_ADD_HARDWARE_INTERFACE macro.
template <class HardwareInterfaceT>
inline absl::StatusOr<MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>>
GetMutableStrictInterfaceHandle(
    const SharedMemoryManager& shared_memory_manager,
    absl::string_view interface_name) {
  INTR_ASSIGN_OR_RETURN(auto handle,
                        GetMutableInterfaceHandle<HardwareInterfaceT>(
                            shared_memory_manager, interface_name));

  INTR_ASSIGN_OR_RETURN(auto icon_state,
                        GetInterfaceHandle<intrinsic_fbs::IconState>(
                            shared_memory_manager, kIconStateInterfaceName));

  return MutableStrictHardwareInterfaceHandle<HardwareInterfaceT>(
      std::move(handle), std::move(icon_state));
}

// Returns information about the exported interfaces from a hardware module.
inline absl::StatusOr<ReadOnlyMemorySegment<SegmentInfo>> GetHardwareModuleInfo(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map) {
  return ReadOnlyMemorySegment<SegmentInfo>::Get(
      segment_name_to_file_descriptor_map, hal::kModuleInfoName);
}

// Extracts the names of the shared memory segments.
inline std::vector<std::string> GetInterfacesFromModuleInfo(
    const SegmentInfo& segment_info) {
  return GetNamesFromSegmentInfo(segment_info);
}

// Extracts the names of the shared memory segments that are marked as required.
//
// Subset of GetInterfacesFromModuleInfo.
inline std::vector<std::string> GetRequiredInterfacesFromModuleInfo(
    const SegmentInfo& segment_info) {
  return GetRequiredInterfaceNamesFromSegmentInfo(segment_info);
}

}  // namespace intrinsic::icon
#endif  // INTRINSIC_ICON_HAL_GET_HARDWARE_INTERFACE_H_
