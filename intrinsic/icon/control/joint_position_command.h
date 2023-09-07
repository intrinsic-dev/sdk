// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_JOINT_POSITION_COMMAND_H_
#define INTRINSIC_ICON_CONTROL_JOINT_POSITION_COMMAND_H_

#include <cstddef>
#include <optional>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/utils/realtime_status_or.h"
#include "intrinsic/kinematics/types/dynamic_limits_check_mode.h"

namespace intrinsic::icon {

// Represents a set of command parameters for joint position control (with
// optional feedforward terms) that is sent to the hardware abstraction layer.
// It further provides the `limits_type`which specifies if either joint
// acceleration limits, joint torque limits, or none of them are to be checked
// against violations.
class JointPositionCommand {
 public:
  // Default constructor to make this play nice with containers and StatusOr.
  JointPositionCommand() : position_(0) {}

  explicit JointPositionCommand(const eigenmath::VectorNd& position)
      : position_(position) {}

  JointPositionCommand(const eigenmath::VectorNd& position,
                       DynamicLimitsCheckMode joint_dynamic_limits_check_mode)
      : position_(position),
        joint_dynamic_limits_check_mode_(joint_dynamic_limits_check_mode) {}

  // Builds the default limits type to annotate a setpoint of this class. The
  // joint command limits type defaults to checking joint accelerations limits.
  static constexpr DynamicLimitsCheckMode DefaultDynamicLimitsCheckMode() {
    return DynamicLimitsCheckMode::kCheckJointAcceleration;
  }

  // Builds a JointPositionCommand object.
  //
  // Returns InvalidArgument if any of the three vectors' sizes don't match up.
  static RealtimeStatusOr<JointPositionCommand> Create(
      const eigenmath::VectorNd& position,
      const std::optional<eigenmath::VectorNd>& velocity_feedforward =
          std::nullopt,
      const std::optional<eigenmath::VectorNd>& acceleration_feedforward =
          std::nullopt,
      DynamicLimitsCheckMode joint_dynamic_limits_check_mode =
          DefaultDynamicLimitsCheckMode());

  const eigenmath::VectorNd& position() const;

  const std::optional<eigenmath::VectorNd>& velocity_feedforward() const;

  const std::optional<eigenmath::VectorNd>& acceleration_feedforward() const;

  inline DynamicLimitsCheckMode joint_dynamic_limits_check_mode() const {
    return joint_dynamic_limits_check_mode_;
  }

  size_t Size() const;

 private:
  JointPositionCommand(
      const eigenmath::VectorNd& position,
      const std::optional<eigenmath::VectorNd>& velocity_feedforward,
      const std::optional<eigenmath::VectorNd>& acceleration_feedforward,
      DynamicLimitsCheckMode joint_dynamic_limits_check_mode);

  eigenmath::VectorNd position_;
  std::optional<eigenmath::VectorNd> velocity_feedforward_ = std::nullopt;
  std::optional<eigenmath::VectorNd> acceleration_feedforward_ = std::nullopt;
  DynamicLimitsCheckMode joint_dynamic_limits_check_mode_ =
      DefaultDynamicLimitsCheckMode();
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_JOINT_POSITION_COMMAND_H_
