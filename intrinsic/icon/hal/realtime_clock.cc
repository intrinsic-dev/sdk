// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/hal/realtime_clock.h"

#include <stdint.h>

#include <memory>
#include <string>
#include <utility>

#include "absl/log/check.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/icon/interprocess/shared_memory_lockstep/shared_memory_lockstep.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/memory_segment.h"
#include "intrinsic/icon/interprocess/shared_memory_manager/shared_memory_manager.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/icon/utils/clock.h"
#include "intrinsic/icon/utils/clock_base.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_macro.h"
#include "intrinsic/util/thread/lockstep.h"

namespace intrinsic::icon {

static constexpr absl::Duration kStartUpLockstepTimeout = absl::Minutes(1);

RealtimeClock::RealtimeClock(
    SharedMemoryLockstep lockstep,
    ReadWriteMemorySegment<RealtimeClockUpdate> realtime_clock_update,
    SharedMemoryManager shm_manager)
    : lockstep_(std::move(lockstep)),
      update_(std::move(realtime_clock_update)),
      shm_manager_(std::move(shm_manager)) {
  // This matches the first EndOperationA in TickBlockingWithTimeout. See
  // comments in TickBlockingWithTimeout.
  // During startup it might take several seconds until both sides of the
  // lockstep are available.
  CHECK_OK(lockstep_->StartOperationAWithTimeout(
      /*timeout=*/kStartUpLockstepTimeout));
}

RealtimeClock::~RealtimeClock() {
  // This matches the final StartOperationA in TickBlockingWithTimeout. See
  // comments in TickBlockingWithTimeout.
  if (RealtimeStatus status = lockstep_->EndOperationA(); !status.ok()) {
    LOG(WARNING) << "Error destructing RealtimeClock: " << status.message();
  }
}

RealtimeStatus RealtimeClock::TickBlockingWithDeadline(
    intrinsic::Time current_timestamp, absl::Time deadline) {
  // This is called from the clock owner's thread. Everything *outside* this
  // method is "Operation A", which is the reason for the inversion here
  // (End, then Start). The initial call to StartOperationA is in the
  // constructor.

  // Store `current_timestamp` before allowing "Operation B" (the control
  // update) to run.
  update_.GetValue().cycle_start_nanoseconds =
      toNSec<int64_t>(current_timestamp);

  INTRINSIC_RT_RETURN_IF_ERROR(lockstep_->EndOperationA());
  // ...
  // RTCL's turn! Cyclic update occurs here in the ICON control process.
  // ...

  // For the final call to TickBlockingWithTimeout(), the
  // StartOperationAWithDeadline() here matches the EndOperationA() in the
  // destructor.
  return lockstep_->StartOperationAWithDeadline(deadline);
}

RealtimeStatus RealtimeClock::Reset(absl::Duration timeout) {
  // Cancel, in case someone is still waiting or about to wait.
  lockstep_->Cancel();
  auto status = lockstep_->Reset(timeout);
  // StartOperationA matches the first EndOperationA in TickBlockingWithTimeout.
  // See comments in TickBlockingWithTimeout.
  return OverwriteIfNotInError(status,
                               lockstep_->StartOperationAWithTimeout(timeout));
}

absl::StatusOr<std::unique_ptr<RealtimeClock>> RealtimeClock::Create(
    absl::string_view hardware_module_name) {
  INTRINSIC_ASSERT_NON_REALTIME();
  std::string lockstep_name = LockstepSegmentName(hardware_module_name);
  SharedMemoryManager shm_manager;
  INTRINSIC_ASSIGN_OR_RETURN(
      SharedMemoryLockstep lockstep,
      CreateSharedMemoryLockstep(shm_manager, lockstep_name));

  std::string update_name =
      RealtimeClockUpdateSegmentName(hardware_module_name);
  INTRINSIC_RETURN_IF_ERROR(
      shm_manager.AddSegmentWithDefaultValue<icon::RealtimeClockUpdate>(
          update_name));

  INTRINSIC_ASSIGN_OR_RETURN(
      ReadWriteMemorySegment<RealtimeClockUpdate> update,
      ReadWriteMemorySegment<RealtimeClockUpdate>::Get(update_name));

  return absl::WrapUnique(new RealtimeClock(
      std::move(lockstep), std::move(update), std::move(shm_manager)));
}

}  // namespace intrinsic::icon
