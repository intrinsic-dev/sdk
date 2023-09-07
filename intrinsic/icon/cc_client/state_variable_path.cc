// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/cc_client/state_variable_path.h"

#include <cstddef>
#include <string>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/common/state_variable_path_constants.h"
#include "intrinsic/icon/common/state_variable_path_util.h"

namespace intrinsic::icon {

namespace {

std::string BuildIndexedArmPath(absl::string_view part_name,
                                absl::string_view field_type_name,
                                size_t index) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kArmTypeNodeName},
       {.name = std::string(field_type_name), .index = index}});
}
}  // namespace

std::string ArmSensedPositionStateVariablePath(absl::string_view part_name,
                                               size_t joint_index) {
  return BuildIndexedArmPath(part_name, kSensedPositionNodeName, joint_index);
}

std::string ArmSensedVelocityStateVariablePath(absl::string_view part_name,
                                               size_t joint_index) {
  return BuildIndexedArmPath(part_name, kSensedVelocityNodeName, joint_index);
}

std::string ArmSensedAccelerationStateVariablePath(absl::string_view part_name,
                                                   size_t joint_index) {
  return BuildIndexedArmPath(part_name, kSensedAccelerationNodeName,
                             joint_index);
}

std::string ArmSensedTorqueStateVariablePath(absl::string_view part_name,
                                             size_t joint_index) {
  return BuildIndexedArmPath(part_name, kSensedTorqueNodeName, joint_index);
}

std::string ArmBaseTwistTipSensedStateVariablePath(
    absl::string_view part_name, TwistDimension twist_dimension) {
  return BuildIndexedArmPath(part_name, kBaseTwistTipSensedNodeNodeName,
                             static_cast<size_t>(twist_dimension));
}

std::string ArmBaseLinearVelocityTipSensedStateVariablePath(
    absl::string_view part_name) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kArmTypeNodeName},
       {.name = kBaseLinearVelocityTipSensedNodeName}});
}

std::string ArmBaseAngularVelocityTipSensedStateVariablePath(
    absl::string_view part_name) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kArmTypeNodeName},
       {.name = kBaseAngularVelocityTipSensedNodeName}});
}

std::string ArmCurrentControlModeStateVariablePath(
    absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kArmTypeNodeName},
                                 {.name = kCurrentControlModeNodeName}});
}

std::string FTWrenchAtTipStateVariablePath(absl::string_view part_name,
                                           WrenchDimension wrench_dimesion) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kFTTypeNodeName},
       {.name = kWrenchAtTipNodeName,
        .index = static_cast<size_t>(wrench_dimesion)}});
}

std::string FTForceMagnitudeAtTipStateVariablePath(
    absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kFTTypeNodeName},
                                 {.name = kForceMagnitudeAtTipNodeName}});
}

std::string FTTorqueMagnitudeAtTipStateVariablePath(
    absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kFTTypeNodeName},
                                 {.name = kTorqueMagnitudeAtTipNodeName}});
}

std::string GripperSensedStateStateVariablePath(absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kGripperTypeNodeName},
                                 {.name = kGripperSensedStateNodeName}});
}

std::string GripperOpeningWidthStateVariablePath(absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kGripperTypeNodeName},
                                 {.name = kGripperOpeningWidthNodeName}});
}

std::string RangefinderDistanceStateVariablePath(absl::string_view part_name) {
  return BuildStateVariablePath({{.name = std::string(part_name)},
                                 {.name = kRangefinderNodeName},
                                 {.name = kRangefinderDistanceNodeName}});
}

std::string ADIODigitalInputStateVariablePath(absl::string_view part_name,
                                              absl::string_view block_name,
                                              size_t signal_index) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kADIOTypeNodeName},
       {.name = kDigitalInputNodeName},
       {.name = std::string(block_name), .index = signal_index}});
}

std::string ADIODigitalOutputStateVariablePath(absl::string_view part_name,
                                               absl::string_view block_name,
                                               size_t signal_index) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kADIOTypeNodeName},
       {.name = kDigitalOutputNodeName},
       {.name = std::string(block_name), .index = signal_index}});
}

std::string ADIOAnalogInputStateVariablePath(absl::string_view part_name,
                                             absl::string_view block_name,
                                             size_t signal_index) {
  return BuildStateVariablePath(
      {{.name = std::string(part_name)},
       {.name = kADIOTypeNodeName},
       {.name = kAnalogInputNodeName},
       {.name = std::string(block_name), .index = signal_index}});
}

std::string SafetyEnableButtonStatusStateVariablePath() {
  return BuildStateVariablePath(
      {{.name = kSafetyTypeNodeName}, {.name = kEnableButtonStatusNodeName}});
}

}  // namespace intrinsic::icon
