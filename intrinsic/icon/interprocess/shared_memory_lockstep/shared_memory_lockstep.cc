// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/interprocess/shared_memory_lockstep/shared_memory_lockstep.h"

#include <string>
#include <utility>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/thread/lockstep.h"

namespace intrinsic::icon {

bool SharedMemoryLockstep::Connected() const {
  if (!memory_segment_.IsValid()) {
    return false;
  }
  return memory_segment_.Header().WriterRefCount() == 2;
}

absl::StatusOr<SharedMemoryLockstep> CreateSharedMemoryLockstep(
    SharedMemoryManager& manager, absl::string_view segment_name) {
  INTRINSIC_RETURN_IF_ERROR(
      manager.AddSegment(std::string(segment_name), Lockstep()));
  return GetSharedMemoryLockstep(segment_name);
}

absl::StatusOr<SharedMemoryLockstep> GetSharedMemoryLockstep(
    absl::string_view segment_name) {
  INTRINSIC_ASSIGN_OR_RETURN(
      auto segment,
      ReadWriteMemorySegment<Lockstep>::Get(std::string(segment_name)));
  return SharedMemoryLockstep(std::move(segment));
}

}  // namespace intrinsic::icon
