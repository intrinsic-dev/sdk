// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/hal/hardware_module_util.h"

#include <set>
#include <string>
#include <utility>
#include <vector>

#include "absl/strings/str_cat.h"
#include "intrinsic/icon/hal/interfaces/hardware_module_state.fbs.h"

namespace intrinsic::icon {

TransitionGuardResult HardwareModuleTransitionGuard(
    intrinsic_fbs::StateCode from, intrinsic_fbs::StateCode to) {
  using intrinsic_fbs::StateCode;
  if (to == StateCode::kFatallyFaulted) {
    return TransitionGuardResult::kAllowed;
  }

  switch (from) {
    case StateCode::kPreparing:
      switch (to) {
        case StateCode::kPrepared:
        case StateCode::kInitFailed:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }
    case StateCode::kPrepared:
      switch (to) {
        case StateCode::kActivating:
        case StateCode::kDeactivating:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }
    case StateCode::kDeactivating:
      switch (to) {
        case StateCode::kDeactivated:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }
    case StateCode::kDeactivated:
      switch (to) {
        case StateCode::kDeactivating:
          return TransitionGuardResult::kNoOp;
        case StateCode::kPreparing:
        case StateCode::kInitFailed:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kActivating:
      switch (to) {
        case StateCode::kActivated:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kActivated:
      switch (to) {
        case StateCode::kMotionDisabling:
        case StateCode::kClearingFaults:
          return TransitionGuardResult::kNoOp;
        case StateCode::kMotionEnabling:
        case StateCode::kDeactivating:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kMotionEnabling:
      switch (to) {
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
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kMotionDisabling:
      switch (to) {
        case StateCode::kFaulted:
        case StateCode::kActivated:
        case StateCode::kDeactivating:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kFaulted:
      switch (to) {
        case StateCode::kClearingFaults:
        case StateCode::kDeactivating:
        case StateCode::kFaulted:
          return TransitionGuardResult::kAllowed;
        default:
          return TransitionGuardResult::kProhibited;
      }

    case StateCode::kClearingFaults:
      switch (to) {
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

namespace {
std::string CreateDotGraphvizStateMachineString(
    const std::vector<std::pair<intrinsic_fbs::StateCode,
                                intrinsic_fbs::StateCode>>& transitions) {
  std::string dot_string = "digraph StateMachine {\n";
  std::set<intrinsic_fbs::StateCode> states;
  for (const auto& transition : transitions) {
    states.insert(transition.first);
    states.insert(transition.second);
  }
  for (const auto& state : states) {
    dot_string += absl::StrCat(
        "  ", intrinsic_fbs::EnumNameStateCode(state), " [label=\"",
        intrinsic_fbs::EnumNameStateCode(state), "\"];\n");
  }

  // Add edges (transitions)
  for (const auto& transition : transitions) {
    dot_string += absl::StrCat(
        "  ", intrinsic_fbs::EnumNameStateCode(transition.first), " -> ",
        intrinsic_fbs::EnumNameStateCode(transition.second), ";\n");
  }

  dot_string += "}\n";
  return dot_string;
}
}  // namespace

std::string CreateDotGraphvizStateMachineString() {
  std::vector<std::pair<intrinsic_fbs::StateCode, intrinsic_fbs::StateCode>>
      transitions;
  for (auto from : intrinsic_fbs::EnumValuesStateCode()) {
    for (auto to : intrinsic_fbs::EnumValuesStateCode()) {
      if (HardwareModuleTransitionGuard(from, to) ==
          TransitionGuardResult::kAllowed) {
        transitions.push_back({from, to});
      }
    }
  }
  return CreateDotGraphvizStateMachineString(transitions);
}

}  // namespace intrinsic::icon
