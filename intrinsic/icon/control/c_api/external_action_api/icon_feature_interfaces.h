// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_FEATURE_INTERFACES_H_
#define INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_FEATURE_INTERFACES_H_

#include <optional>
#include <utility>

#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/c_api/c_feature_interfaces.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_or.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic::icon {

// These classes wrap a C API FeatureInterface and allow C++-based Action
// plugins to interact with it via idiomatic C++ function calls.

class IconConstJointPositionCommandInterface {
 public:
  IconConstJointPositionCommandInterface(
      const XfaIconFeatureInterfaceJointPositionCommandInterface*
          joint_position_c,
      XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable
          joint_position_vtable)
      : joint_position_c_(joint_position_c),
        joint_position_vtable_(std::move(joint_position_vtable)) {}

  // Returns the previous position command, including any velocity and
  // acceleration feedforward values.
  JointPositionCommand PreviousPositionSetpoints() const;

 private:
  const XfaIconFeatureInterfaceJointPositionCommandInterface* joint_position_c_;
  XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable
      joint_position_vtable_;
};

class IconJointPositionCommandInterface {
 public:
  IconJointPositionCommandInterface(
      XfaIconFeatureInterfaceJointPositionCommandInterface* joint_position_c,
      XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable
          joint_position_vtable)
      : joint_position_c_(joint_position_c),
        joint_position_vtable_(std::move(joint_position_vtable)) {}

  // Sends the given position setpoints with velocity and torque feedforward
  // values.
  //
  // Returns an error if the setpoints are invalid, i.e. they contain the wrong
  // number of values or violate any limits.
  RealtimeStatus SetPositionSetpoints(const JointPositionCommand& setpoints);

  // Returns the previous position command, including any velocity and
  // acceleration feedforward values.
  JointPositionCommand PreviousPositionSetpoints() const;

 private:
  XfaIconFeatureInterfaceJointPositionCommandInterface* joint_position_c_;
  XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable
      joint_position_vtable_;
};

class IconJointPositionSensor {
 public:
  IconJointPositionSensor(
      const XfaIconFeatureInterfaceJointPositionSensor* joint_position_sensor_c,
      XfaIconFeatureInterfaceJointPositionSensorVtable
          joint_position_sensor_vtable)
      : joint_position_sensor_c_(joint_position_sensor_c),
        joint_position_sensor_vtable_(std::move(joint_position_sensor_vtable)) {
  }

  // Returns the sensed position of all joints for this part.
  JointStateP GetSensedPosition() const;

 private:
  const XfaIconFeatureInterfaceJointPositionSensor* joint_position_sensor_c_ =
      nullptr;
  XfaIconFeatureInterfaceJointPositionSensorVtable
      joint_position_sensor_vtable_;
};

class IconJointVelocityEstimator {
 public:
  IconJointVelocityEstimator(
      const XfaIconFeatureInterfaceJointVelocityEstimator*
          joint_velocity_estimator_c,
      XfaIconFeatureInterfaceJointVelocityEstimatorVtable
          joint_velocity_estimator_vtable)
      : joint_velocity_estimator_c_(joint_velocity_estimator_c),
        joint_velocity_estimator_vtable_(
            std::move(joint_velocity_estimator_vtable)) {}

  // Returns a velocity estimate of all joints for this part.
  JointStateV GetVelocityEstimate() const;

 private:
  const XfaIconFeatureInterfaceJointVelocityEstimator*
      joint_velocity_estimator_c_ = nullptr;
  XfaIconFeatureInterfaceJointVelocityEstimatorVtable
      joint_velocity_estimator_vtable_;
};

class IconJointLimits {
 public:
  IconJointLimits(const XfaIconFeatureInterfaceJointLimits* joint_limits_c,
                  XfaIconFeatureInterfaceJointLimitsVtable joint_limits_vtable)
      : joint_limits_c_(joint_limits_c),
        joint_limits_vtable_(std::move(joint_limits_vtable)) {}

  // Returns the application limits for the joints of this part. These are
  // configured, for instance for a workcell. Actions should use these joint
  // limits by default and reject any user commands that exceed them.
  //
  // That said, an Action may exploit the margin between application limits and
  // system limits (see below) to better realize a user command. For example, a
  // small overshoot in jerk is acceptable, if it allows achieving velocity or
  // acceleration closer to what the user requested.
  //
  // Values of +/- std::numeric_limits<double>::infinity() designate
  // "unlimited".
  JointLimits GetApplicationLimits() const;

  // Returns the system limits for the joints of this part.
  // These are hard limits as reported by the hardware itself, and ICON *must
  // not* exceed them. If any Action commands motion outside of the system
  // limits, ICON will terminate that Action immediately, and fault the robot.
  // Values of +/- std::numeric_limits<double>::infinity() designate
  // "unlimited".
  JointLimits GetSystemLimits() const;

 private:
  const XfaIconFeatureInterfaceJointLimits* joint_limits_c_ = nullptr;
  XfaIconFeatureInterfaceJointLimitsVtable joint_limits_vtable_;
};

class IconConstForceTorqueSensor {
 public:
  IconConstForceTorqueSensor(
      const XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor_c,
      XfaIconFeatureInterfaceForceTorqueSensorVtable force_torque_sensor_vtable)
      : force_torque_sensor_c_(force_torque_sensor_c),
        force_torque_sensor_vtable_(std::move(force_torque_sensor_vtable)) {}

  // Returns the filtered wrench at the tip of the kinematic chain, compensated
  // for support mass and bias.
  // Support mass and bias are configured per workcell and
  // not directly exposed to plugin Actions.
  Wrench WrenchAtTip() const;

 private:
  const XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor_c_ =
      nullptr;
  XfaIconFeatureInterfaceForceTorqueSensorVtable force_torque_sensor_vtable_;
};

class IconForceTorqueSensor {
 public:
  IconForceTorqueSensor(
      XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor_c,
      XfaIconFeatureInterfaceForceTorqueSensorVtable force_torque_sensor_vtable)
      : force_torque_sensor_c_(force_torque_sensor_c),
        force_torque_sensor_vtable_(std::move(force_torque_sensor_vtable)) {}

  // Returns the filtered wrench at the tip of the kinematic chain, compensated
  // for support mass and bias.
  // Support mass and bias are configured per workcell and
  // not directly exposed to plugin Actions.
  Wrench WrenchAtTip() const;
  // Request a taring of the sensor. If the forces acting on the sensor do not
  // change, the sensor will read a zero wrench in the next cycle.
  RealtimeStatus Tare();

 private:
  XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor_c_ = nullptr;
  XfaIconFeatureInterfaceForceTorqueSensorVtable force_torque_sensor_vtable_;
};

class IconManipulatorKinematics {
 public:
  IconManipulatorKinematics(const XfaIconFeatureInterfaceManipulatorKinematics*
                                manipulator_kinematics_c,
                            XfaIconFeatureInterfaceManipulatorKinematicsVtable
                                manipulator_kinematics_vtable)
      : manipulator_kinematics_c_(manipulator_kinematics_c),
        manipulator_kinematics_vtable_(
            std::move(manipulator_kinematics_vtable)) {}

  // Returns the base to tip transform for the given `dof_positions`. Assumes
  // the kinematic model is a chain and returns an error otherwise.
  RealtimeStatusOr<Pose3d> ComputeChainFK(
      const JointStateP dof_positions) const;
  // Returns the base to tip jacobian for the given `dof_positions`. Assumes
  // the kinematic model is a chain and returns an error otherwise.
  RealtimeStatusOr<eigenmath::Matrix6Nd> ComputeChainJacobian(
      const JointStateP dof_positions) const;

 private:
  const XfaIconFeatureInterfaceManipulatorKinematics*
      manipulator_kinematics_c_ = nullptr;
  XfaIconFeatureInterfaceManipulatorKinematicsVtable
      manipulator_kinematics_vtable_;
};

struct IconFeatureInterfaces {
  std::optional<IconJointPositionCommandInterface> joint_position;
  std::optional<IconJointPositionSensor> joint_position_sensor;
  std::optional<IconJointVelocityEstimator> joint_velocity_estimator;
  std::optional<IconJointLimits> joint_limits;
  std::optional<IconForceTorqueSensor> force_torque_sensor;
  std::optional<IconManipulatorKinematics> manipulator_kinematics;
};

struct IconConstFeatureInterfaces {
  std::optional<IconConstJointPositionCommandInterface> joint_position;
  std::optional<IconJointPositionSensor> joint_position_sensor;
  std::optional<IconJointVelocityEstimator> joint_velocity_estimator;
  std::optional<IconJointLimits> joint_limits;
  std::optional<IconConstForceTorqueSensor> force_torque_sensor;
  std::optional<IconManipulatorKinematics> manipulator_kinematics;
};

// Creates instances of the C++ class (see above) for any non-null pointers in
// `const_feature_interfaces`, using the function pointers from
// `feature_interface_vtable`.
//
// Sets the entries for interfaces whose pointers are nullptr to std::nullopt.
const IconConstFeatureInterfaces FromCApiFeatureInterfaces(
    XfaIconConstFeatureInterfacesForSlot const_feature_interfaces,
    const XfaIconFeatureInterfaceVtable feature_interface_vtable);

// Creates instances of the C++ class (see above) for any non-null pointers in
// `feature_interfaces`, using the function pointers from
// `feature_interface_vtable`.
//
// Sets the entries for interfaces whose pointers are nullptr to std::nullopt.
IconFeatureInterfaces FromCApiFeatureInterfaces(
    XfaIconFeatureInterfacesForSlot feature_interfaces,
    XfaIconFeatureInterfaceVtable feature_interface_vtable);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_EXTERNAL_ACTION_API_ICON_FEATURE_INTERFACES_H_
