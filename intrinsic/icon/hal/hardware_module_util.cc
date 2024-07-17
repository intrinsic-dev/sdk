// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/hardware_module_util.h"

#include "intrinsic/icon/hal/interfaces/hardware_module_state_generated.h"

namespace intrinsic::icon {

TransitionGuardResult HardwareModuleTransitionGuard(
    intrinsic_fbs::StateCode from, intrinsic_fbs::StateCode to) {
  using intrinsic_fbs::StateCode;
  if (to == StateCode::kFatallyFaulted) {
    return TransitionGuardResult::kAllowed;
  }

  switch (from) {
    case StateCode::kDeactivating:
      return to == StateCode::kDeactivated ? TransitionGuardResult::kAllowed
                                           : TransitionGuardResult::kProhibited;

    case StateCode::kDeactivated:
      switch (to) {
        case StateCode::kDeactivating:
          return TransitionGuardResult::kNoOp;
        case StateCode::kActivating:
        case StateCode::kInitFailed:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kActivating:
      switch (to) {
        case StateCode::kActivated:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kActivated:
      switch (to) {
        case StateCode::kMotionDisabling:
        case StateCode::kClearingFaults:
          return TransitionGuardResult::kNoOp;
        case StateCode::kActivating:
        case StateCode::kMotionEnabling:
        case StateCode::kDeactivating:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kMotionEnabling:
      switch (to) {
        case StateCode::kActivating:
        case StateCode::kDeactivating:
        case StateCode::kMotionEnabled:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kMotionEnabled:
      switch (to) {
        case StateCode::kMotionEnabling:
        case StateCode::kClearingFaults:
          return TransitionGuardResult::kNoOp;
        case StateCode::kMotionDisabling:
        case StateCode::kFaulted:
        case StateCode::kDeactivating:
        case StateCode::kActivating:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kMotionDisabling:
      switch (to) {
        case StateCode::kFaulted:
        case StateCode::kActivated:
        case StateCode::kActivating:
        case StateCode::kDeactivating:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kFaulted:
      switch (to) {
        case StateCode::kClearingFaults:
        case StateCode::kDeactivating:
        case StateCode::kActivating:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kClearingFaults:
      switch (to) {
        case StateCode::kActivating:
        case StateCode::kDeactivating:
        case StateCode::kFaulted:
        case StateCode::kActivated:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kInitFailed:
      return TransitionGuardResult::kProhibited;

    case StateCode::kFatallyFaulted:
      return TransitionGuardResult::kProhibited;
  }
  return TransitionGuardResult::kProhibited;
}

}  // namespace intrinsic::icon
