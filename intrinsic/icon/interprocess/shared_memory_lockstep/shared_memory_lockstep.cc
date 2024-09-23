// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_lockstep/shared_memory_lockstep.h"

#include <utility>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/domain_socket_utils.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/lockstep.h"

namespace intrinsic::icon {

namespace {

absl::StatusOr<SharedMemoryLockstep> GetSharedMemoryLockstep(
    const SegmentNameToFileDescriptorMap& segment_name_to_file_descriptor_map,
    absl::string_view memory_name) {
  INTR_ASSIGN_OR_RETURN(auto segment,
                        ReadWriteMemorySegment<Lockstep>::Get(
                            segment_name_to_file_descriptor_map, memory_name));
  return SharedMemoryLockstep(std::move(segment));
}

}  // namespace

bool SharedMemoryLockstep::Connected() const {
  if (!memory_segment_.IsValid()) {
    return false;
  }
  return memory_segment_.Header().WriterRefCount() == 2;
}

absl::StatusOr<SharedMemoryLockstep> CreateSharedMemoryLockstep(
    SharedMemoryManager& manager, absl::string_view memory_name) {
  INTR_RETURN_IF_ERROR(manager.AddSegment(memory_name, false, Lockstep()));

  INTR_ASSIGN_OR_RETURN(
      auto segment, manager.Get<ReadWriteMemorySegment<Lockstep>>(memory_name));

  return SharedMemoryLockstep(std::move(segment));
}
absl::StatusOr<SharedMemoryLockstep> GetSharedMemoryLockstep(
    const SharedMemoryManager& manager, absl::string_view memory_name) {
  return GetSharedMemoryLockstep(manager.SegmentNameToFileDescriptorMap(),
                                 memory_name);
}

}  // namespace intrinsic::icon
