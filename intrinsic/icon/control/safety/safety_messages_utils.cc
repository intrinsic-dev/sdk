// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/control/safety/safety_messages_utils.h"

#include <bitset>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

#include "intrinsic/icon/control/safety/extern/safety_status_generated.h"
#include "intrinsic/icon/control/safety/safety_messages_generated.h"

namespace intrinsic::safety::messages {

flatbuffers::DetachedBuffer BuildSafetyStatusMessage(
    ModeOfSafeOperation mode_of_safe_operation,
    ButtonStatus estop_button_status, ButtonStatus enable_button_status,
    RequestedBehavior requested_behavior) {
  flatbuffers::FlatBufferBuilder builder;
  builder.ForceDefaults(true);
  builder.Finish(CreateSafetyStatusMessage(
      builder, mode_of_safe_operation, estop_button_status,
      enable_button_status, requested_behavior));
  return builder.Release();
}

void SetSafetyStatusMessage(
    const ::intrinsic::safety::messages::ModeOfSafeOperation
        mode_of_safe_operation,
    const ::intrinsic::safety::messages::ButtonStatus estop_button_status,
    const ::intrinsic::safety::messages::ButtonStatus enable_button_status,
    const ::intrinsic::safety::messages::RequestedBehavior requested_behavior,
    ::intrinsic::safety::messages::SafetyStatusMessage& message) {
  message.mutate_mode_of_safe_operation(mode_of_safe_operation);
  message.mutate_estop_button_status(estop_button_status);
  message.mutate_enable_button_status(enable_button_status);
  message.mutate_requested_behavior(requested_behavior);
}

ModeOfSafeOperation ExtractModeOfSafeOperation(
    const std::bitset<8>& safety_inputs) {
  bool is_auto_mode_set = safety_inputs[AsIndex(SafetyStatusBit::MSO_AUTO)];
  bool is_t1_mode_set = safety_inputs[AsIndex(SafetyStatusBit::MSO_T1)];

  // Return UNKNOWN, if both bits (AUTO and T1) are identical.
  if (is_auto_mode_set == is_t1_mode_set) {
    return ModeOfSafeOperation::UNKNOWN;
  }
  return is_auto_mode_set ? ModeOfSafeOperation::AUTOMATIC
                          : ModeOfSafeOperation::TEACH_PENDANT_1;
}

ButtonStatus ExtractEStopButtonStatus(const std::bitset<8>& safety_inputs) {
  // Checks that the e-stop button is supported by checking if either of the
  // ModeOfSafeOperation (MSO) bits is `true`. If both bits are `false`, the
  // e-stop button and MSO status are not supported. This was the case for early
  // versions of the safety logic (copper release).
  const bool is_auto_mode_set =
      safety_inputs[AsIndex(SafetyStatusBit::MSO_AUTO)];
  const bool is_t1_mode_set = safety_inputs[AsIndex(SafetyStatusBit::MSO_T1)];

  const bool is_button_state_supported = is_auto_mode_set != is_t1_mode_set;

  if (!is_button_state_supported) {
    return ButtonStatus::NOT_AVAILABLE;
  }

  // E-Stop is Active-Low, i.e. the signal is low/false, when the button is
  // engaged.
  return safety_inputs[AsIndex(SafetyStatusBit::E_STOP)]
             ? ButtonStatus::DISENGAGED
             : ButtonStatus::ENGAGED;
}

ButtonStatus ExtractEnableButtonStatus(const std::bitset<8>& safety_inputs) {
  // Checks that the enable button is supported by checking if either of the
  // ModeOfSafeOperation (MSO) bits is `true`. If both bits are `false`, the
  // enable button and MSO status are not supported. This was the case for early
  // versions of the safety logic (copper release).
  const bool is_auto_mode_set =
      safety_inputs[AsIndex(SafetyStatusBit::MSO_AUTO)];
  const bool is_t1_mode_set = safety_inputs[AsIndex(SafetyStatusBit::MSO_T1)];

  const bool is_button_state_supported = is_auto_mode_set != is_t1_mode_set;

  if (!is_button_state_supported) {
    return ButtonStatus::NOT_AVAILABLE;
  }

  // Enable is ENGAGED, if and only if both SS1t and MSO_T1 are HIGH
  return safety_inputs[AsIndex(SafetyStatusBit::SS1_T)] && is_t1_mode_set
             ? ButtonStatus::ENGAGED
             : ButtonStatus::DISENGAGED;
}

RequestedBehavior ExtractRequestedBehavior(
    const std::bitset<8>& safety_inputs) {
  if (safety_inputs[AsIndex(SafetyStatusBit::SS1_T)] == true) {
    return RequestedBehavior::NORMAL_OPERATION;
  }
  if (safety_inputs[AsIndex(SafetyStatusBit::SS1_T)] == false) {
    // E_STOP is active low, i.e. if pressed the signal is 0.
    if (safety_inputs[AsIndex(SafetyStatusBit::E_STOP)] == false) {
      return RequestedBehavior::SAFE_STOP_1_TIME_MONITORED;
    } else {
      return RequestedBehavior::SAFE_STOP_2_TIME_MONITORED;
    }
  }

  return RequestedBehavior::UNKNOWN;
}

}  // namespace intrinsic::safety::messages
