// Copyright 2023 Intrinsic Innovation LLC

// This file contains state variable path builder functions to easily create
// those paths for each available robot system state field.
#ifndef INTRINSIC_ICON_CC_CLIENT_STATE_VARIABLE_PATH_H_
#define INTRINSIC_ICON_CC_CLIENT_STATE_VARIABLE_PATH_H_

#include <string>

#include "absl/strings/string_view.h"

namespace intrinsic::icon {

// Generates a state variable path for a single sensed joint position.
//
// The referenced field has the type: double
std::string ArmSensedPositionStateVariablePath(absl::string_view part_name,
                                               size_t joint_index);

// Generates a state variable path for a single sensed joint velocity.
//
// The referenced field has the type: double
std::string ArmSensedVelocityStateVariablePath(absl::string_view part_name,
                                               size_t joint_index);

// Generates a state variable path for a single sensed joint acceleration.
//
// The referenced field has the type: double
std::string ArmSensedAccelerationStateVariablePath(absl::string_view part_name,
                                                   size_t joint_index);

// Generates a state variable path for a single sensed joint torque.
//
// The referenced field has the type: double
std::string ArmSensedTorqueStateVariablePath(absl::string_view part_name,
                                             size_t joint_index);

enum class TwistDimension { X, Y, Z, RX, RY, RZ };

// Generates a state variable path for a single sensed twist entry. The twist is
// calculated for the tip in the robot's base frame based on the sensed joint
// velocities.
//
// The referenced field has the type: double
std::string ArmBaseTwistTipSensedStateVariablePath(
    absl::string_view part_name, TwistDimension twist_dimension);

// Generates a state variable path for the Cartesian linear velocity
// magnitude (also called Euclidean or l^2-Norm) of the arm tip in the robot's
// base frame.
//
// The referenced field has the type: double
std::string ArmBaseLinearVelocityTipSensedStateVariablePath(
    absl::string_view part_name);

// Generates a state variable path for the Cartesian angular velocity
// magnitude (also called Euclidean or l^2-Norm) of the arm tip in the robot's
// base frame.
//
// The referenced field has the type: double
std::string ArmBaseAngularVelocityTipSensedStateVariablePath(
    absl::string_view part_name);

// Generates a state variable path for currently used control mode. The value
// corresponds to the values of the enum
// ::intrinsic_proto::icon::PartControlMode.
//
// The referenced field has the type: int64
std::string ArmCurrentControlModeStateVariablePath(absl::string_view part_name);

enum class WrenchDimension { X, Y, Z, RX, RY, RZ };

// Generates a state variable path for a single value of a wrench at the tip of
// the robot arm.
//
// The referenced field has the type: double
std::string FTWrenchAtTipStateVariablePath(absl::string_view part_name,
                                           WrenchDimension wrench_dimesion);

// Generates a state variable path for the magnitude (Euclidean or l^2-Norm) of
// the
// **force** sensed at the force torque sensor in the frame of the arm tip.
//
// The referenced field has the type: double
//
//     part_name: Name of the force torque sensor part.
//
// Returns a generated state variable path string.
std::string FTForceMagnitudeAtTipStateVariablePath(absl::string_view part_name);

// Generates a state variable path for the magnitude (Euclidean or l^2-Norm) of
// the
// **torque** sensed at the force torque sensor in the frame of the arm tip.
//
// The referenced field has the type: double
//
//     part_name: Name of the force torque sensor part.
//
// Returns a generated state variable path string.
std::string FTTorqueMagnitudeAtTipStateVariablePath(
    absl::string_view part_name);

// Generates a state variable path for sensed state of the gripper.
//
// The referenced field has the type: int64
//   The enum values in this field are reported as integer values but
//   correspond to the proto enum
//   ::intrinsic_proto::icon::GripperState_SensedState.
//
//     part_name: Name of the gripper part.
//
// Returns a generated state variable path string.
std::string GripperSensedStateStateVariablePath(absl::string_view part_name);

// Generates a state variable path for the opening width of the gripper.
//
// The referenced field has the type: double
//
//  Args:
//    part_name: Name of the gripper part.
//
//  Returns:
//    Generated state variable path string.
std::string GripperOpeningWidthStateVariablePath(absl::string_view part_name);

// Generates a state variable path for the status of digital input of the signal
// at `signal_index` in block `block_name`.
//
// The referenced field has the type: bool
//
//     block_name: Name of the signal block.
//     signal_index: Index in the block.
//     part_name: Name of the adio part.
//
// Returns a generated state variable path string.
std::string ADIODigitalInputStateVariablePath(absl::string_view part_name,
                                              absl::string_view block_name,
                                              size_t signal_index);

// Generates a state variable path for the status of digital output of the
// signal at `signal_index` in block `block_name`.
//
// The referenced field has the type: bool
//
//     block_name: Name of the signal block.
//     signal_index: Index in the block.
//     part_name: Name of the adio part.
//
// Returns a generated state variable path string.
std::string ADIODigitalOutputStateVariablePath(absl::string_view part_name,
                                               absl::string_view block_name,
                                               size_t signal_index);

// Generates a state variable path for the status of analog input of the signal
// at `signal_index` in block `block_name`.
//
// The referenced field has the type: double
//
//     block_name: Name of the signal block.
//     signal_index: Index in the block.
//     part_name: Name of the adio part.
//
// Returns a generated state variable path string.
std::string ADIOAnalogInputStateVariablePath(absl::string_view part_name,
                                             absl::string_view block_name,
                                             size_t signal_index);

// Generates a state variable path for the sensed distance of the rangefinder.
//
// The referenced field has the type: double
//
//  Args:
//    part_name: Name of the rangefinder part.
//
//  Returns:
//    Generated state variable path string.
std::string RangefinderDistanceStateVariablePath(absl::string_view part_name);

// Generates a state variable path for the state of the enable safety button.
//
// The referenced field has the type: int64
//   The enum values in this field are reported as integer values but
//   correspond to the proto enum
//   intrinsic_proto::icon::ButtonStatus.
//
// Returns a generated state variable path string.
std::string SafetyEnableButtonStatusStateVariablePath();

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CC_CLIENT_STATE_VARIABLE_PATH_H_
