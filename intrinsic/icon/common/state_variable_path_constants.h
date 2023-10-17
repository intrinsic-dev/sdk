// Copyright 2023 Intrinsic Innovation LLC

// File to declare all strings used for state variable paths.
#ifndef INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_CONSTANTS_H_
#define INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_CONSTANTS_H_

#include <cstddef>

namespace intrinsic::icon {

// Maximum length a state variable path node can have.
constexpr size_t kMaxNodeNameLength = 40;
// Prefix that is used to identify a state variable path.
constexpr const char* kStateVariablePathPrefix = "@";
// Separator used to split a state variable path into nodes.
constexpr const char* kStateVariablePathSeparator = ".";

// Strings for part identification.
constexpr const char* kArmTypeNodeName = "ArmPart";
constexpr const char* kFTTypeNodeName = "ForceTorqueSensorPart";
constexpr const char* kADIOTypeNodeName = "ADIOPart";
constexpr const char* kGripperTypeNodeName = "GripperPart";
constexpr const char* kRangefinderNodeName = "RangefinderPart";

// Strings for additional nodes that are not parts.
constexpr const char* kSafetyTypeNodeName = "Safety";

// Arm
constexpr const char* kSensedPositionNodeName = "sensed_position";
constexpr const char* kSensedVelocityNodeName = "sensed_velocity";
constexpr const char* kSensedAccelerationNodeName = "sensed_acceleration";
constexpr const char* kSensedTorqueNodeName = "sensed_torque";
constexpr const char* kBaseTwistTipSensedNodeNodeName = "base_twist_tip_sensed";
constexpr const char* kBaseLinearVelocityTipSensedNodeName =
    "base_linear_velocity_tip_sensed";
constexpr const char* kBaseAngularVelocityTipSensedNodeName =
    "base_angular_velocity_tip_sensed";
constexpr const char* kCurrentControlModeNodeName = "current_control_mode";

// Force torque sensor
constexpr const char* kWrenchAtTipNodeName = "wrench_at_tip";
constexpr const char* kForceMagnitudeAtTipNodeName = "force_magnitude_at_tip";
constexpr const char* kTorqueMagnitudeAtTipNodeName = "torque_magnitude_at_tip";

// Simple gripper
constexpr const char* kGripperSensedStateNodeName = "sensed_state";
constexpr const char* kGripperOpeningWidthNodeName = "opening_width";

// ADIO
constexpr const char* kDigitalInputNodeName = "di";
constexpr const char* kDigitalOutputNodeName = "do";
constexpr const char* kAnalogInputNodeName = "ai";

// Rangefinder
constexpr const char* kRangefinderDistanceNodeName = "distance";

// Safety
constexpr const char* kEnableButtonStatusNodeName = "enable_button_status";

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_COMMON_STATE_VARIABLE_PATH_CONSTANTS_H_
