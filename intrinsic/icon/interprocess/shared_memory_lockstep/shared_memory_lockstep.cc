// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/interprocess/shared_memory_lockstep/shared_memory_lockstep.h"

#include <string>
#include <utility>

#include "absl/status/statusor.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/thread/lockstep.h"

namespace intrinsic::icon {

bool SharedMemoryLockstep::Connected() const {
  if (!memory_segment_.IsValid()) {
    return false;
  }
  return memory_segment_.Header().WriterRefCount() == 2;
}

absl::StatusOr<SharedMemoryLockstep> CreateSharedMemoryLockstep(
    SharedMemoryManager& manager, const MemoryName& memory_name) {
  INTR_RETURN_IF_ERROR(manager.AddSegment(memory_name, Lockstep()));
  return GetSharedMemoryLockstep(memory_name);
}

absl::StatusOr<SharedMemoryLockstep> GetSharedMemoryLockstep(
    const MemoryName& memory_name) {
  INTR_ASSIGN_OR_RETURN(auto segment,
                        ReadWriteMemorySegment<Lockstep>::Get(memory_name));
  return SharedMemoryLockstep(std::move(segment));
}

}  // namespace intrinsic::icon
