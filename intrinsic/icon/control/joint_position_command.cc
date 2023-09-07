// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/joint_position_command.h"

#include <cstddef>
#include <optional>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_or.h"
#include "intrinsic/kinematics/types/dynamic_limits_check_mode.h"

namespace intrinsic::icon {

RealtimeStatusOr<JointPositionCommand> JointPositionCommand::Create(
    const eigenmath::VectorNd& position,
    const std::optional<eigenmath::VectorNd>& velocity_feedforward,
    const std::optional<eigenmath::VectorNd>& acceleration_feedforward,
    const DynamicLimitsCheckMode joint_dynamic_limits_check_mode) {
  if (velocity_feedforward.has_value() &&
      velocity_feedforward->size() != position.size()) {
    return InvalidArgumentError(RealtimeStatus::StrCat(
        "Velocity feedforward has ", velocity_feedforward->size(),
        " values, but position setpoints have ", position.size()));
  }
  if (acceleration_feedforward.has_value() &&
      acceleration_feedforward->size() != position.size()) {
    return InvalidArgumentError(RealtimeStatus::StrCat(
        "Acceleration feedforward has ", acceleration_feedforward->size(),
        " values, but position setpoints have ", position.size()));
  }

  return JointPositionCommand(position, velocity_feedforward,
                              acceleration_feedforward,
                              joint_dynamic_limits_check_mode);
}

const eigenmath::VectorNd& JointPositionCommand::position() const {
  return position_;
}

const std::optional<eigenmath::VectorNd>&
JointPositionCommand::velocity_feedforward() const {
  return velocity_feedforward_;
}

const std::optional<eigenmath::VectorNd>&
JointPositionCommand::acceleration_feedforward() const {
  return acceleration_feedforward_;
}

size_t JointPositionCommand::Size() const { return position_.size(); }

JointPositionCommand::JointPositionCommand(
    const eigenmath::VectorNd& position,
    const std::optional<eigenmath::VectorNd>& velocity_feedforward,
    const std::optional<eigenmath::VectorNd>& acceleration_feedforward,
    const DynamicLimitsCheckMode joint_dynamic_limits_check_mode)
    : position_(position),
      velocity_feedforward_(velocity_feedforward),
      acceleration_feedforward_(acceleration_feedforward),
      joint_dynamic_limits_check_mode_(joint_dynamic_limits_check_mode) {}

}  // namespace intrinsic::icon
