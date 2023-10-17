// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_SAFETY_SAFETY_MESSAGES_UTILS_H_
#define INTRINSIC_ICON_CONTROL_SAFETY_SAFETY_MESSAGES_UTILS_H_

#include <bitset>
#include <cstdint>
#include <string>
#include <type_traits>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/safety/safety_messages_generated.h"

namespace intrinsic::safety::messages {

// Build a SafetyStatusMessage.
flatbuffers::DetachedBuffer BuildSafetyStatusMessage(
    ModeOfSafeOperation mode_of_safe_operation = ModeOfSafeOperation::UNKNOWN,
    ButtonStatus estop_button_status = ButtonStatus::UNKNOWN,
    ButtonStatus enable_button_status = ButtonStatus::UNKNOWN,
    RequestedBehavior requested_behavior = RequestedBehavior::UNKNOWN);

template <typename EnumType>
constexpr auto AsIndex(const EnumType value) ->
    typename std::underlying_type_t<EnumType> {
  return static_cast<typename std::underlying_type_t<EnumType>>(value);
}

// Extract ModeOfSafeOperation from safety inputs.
// The safety inputs are expected to follow the order as in
// safety::messages::SafetyStatusBit.
ModeOfSafeOperation ExtractModeOfSafeOperation(
    const std::bitset<8>& safety_inputs);

// Extract the status of the e-stop button from safety inputs.
// The safety inputs are expected to follow the order as in
// safety::messages::SafetyStatusBit.
ButtonStatus ExtractEStopButtonStatus(const std::bitset<8>& safety_inputs);

// Extract the status of the enable button from safety inputs.
// The safety inputs are expected to follow the order as in
// safety::messages::SafetyStatusBit.
ButtonStatus ExtractEnableButtonStatus(const std::bitset<8>& safety_inputs);

// Extract the requested behavior from safety inputs.
// The safety inputs are expected to follow the order as in
// safety::messages::SafetyStatusBit.
RequestedBehavior ExtractRequestedBehavior(const std::bitset<8>& safety_inputs);

}  // namespace intrinsic::safety::messages

#endif  // INTRINSIC_ICON_CONTROL_SAFETY_SAFETY_MESSAGES_UTILS_H_
