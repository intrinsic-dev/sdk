// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_C_FEATURE_INTERFACES_H_
#define INTRINSIC_ICON_CONTROL_C_API_C_FEATURE_INTERFACES_H_

#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/////////////////////////////////////////////////
// JointPositionCommandInterface FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceJointPositionCommandInterface;

struct XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable {
  // Sends the given position setpoints with optional velocity and acceleration
  // feedforward values. The caller is responsible for ensuring that velocity
  // and acceleration values (if provided) are kinematically consistent.
  //
  // Returns an error if the setpoints are invalid, i.e. they contain the wrong
  // number of values or violate position, velocity or acceleration limits.
  //
  // Returns an error if the part is currently not in position mode.
  XfaIconRealtimeStatus (*set_position_setpoints)(
      XfaIconFeatureInterfaceJointPositionCommandInterface* self,
      const XfaIconJointPositionCommand* const setpoints);

  // Returns the setpoints from the previous control cycle.
  XfaIconJointPositionCommand (*previous_position_setpoints)(
      const XfaIconFeatureInterfaceJointPositionCommandInterface* self);
};

/////////////////////////////////////////////////
// JointPositionSensor FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceJointPositionSensor;

struct XfaIconFeatureInterfaceJointPositionSensorVtable {
  // Returns the current joint positions in radians.
  XfaIconJointStateP (*get_sensed_position)(
      const XfaIconFeatureInterfaceJointPositionSensor* self);
};

/////////////////////////////////////////////////
// JointVelocityEstimator FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceJointVelocityEstimator;

struct XfaIconFeatureInterfaceJointVelocityEstimatorVtable {
  // Returns the current joint velocity estimates in radians per second.
  XfaIconJointStateV (*get_velocity_estimate)(
      const XfaIconFeatureInterfaceJointVelocityEstimator* self);
};

/////////////////////////////////////////////////
// JointLimits FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceJointLimits;

struct XfaIconFeatureInterfaceJointLimitsVtable {
  // Returns the application limits. Actions should use these joint limits by
  // default and reject any user commands that exceed them.
  XfaIconJointLimits (*get_application_limits)(
      const XfaIconFeatureInterfaceJointLimits* self);
  // Returns the system limits. An action must not command motions beyond these
  // limits. ICON monitors this at a low level and faults if the maximum limits
  // are violated.
  XfaIconJointLimits (*get_system_limits)(
      const XfaIconFeatureInterfaceJointLimits* self);
};

/////////////////////////////////////////////////
// ForceTorqueSensor FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceForceTorqueSensor;

struct XfaIconFeatureInterfaceForceTorqueSensorVtable {
  // Filtered wrench at the tip compensated for support mass and bias.
  XfaIconWrench (*wrench_at_tip)(
      const XfaIconFeatureInterfaceForceTorqueSensor* self);
  // Requests a taring of the sensor. ICON will apply the current filtered
  // sensor reading as a bias to all future readings. That is, if the forces
  // acting on the sensor do not change, a call to WrenchAtTip() in the next
  // control cycle will return an all-zero Wrench.
  XfaIconRealtimeStatus (*tare)(XfaIconFeatureInterfaceForceTorqueSensor* self);
};

/////////////////////////////////////////////////
// ManipulatorKinematics FeatureInterface
/////////////////////////////////////////////////
struct XfaIconFeatureInterfaceManipulatorKinematics;

struct XfaIconFeatureInterfaceManipulatorKinematicsVtable {
  // Writes the base to tip Jacobian for the given `dof_positions` into
  // `jacobian_out`. Assumes the kinematic model is a chain and returns an error
  // otherwise.
  // Caller owns `jacobian_out`.
  XfaIconRealtimeStatus (*compute_chain_jacobian)(
      const XfaIconFeatureInterfaceManipulatorKinematics* self,
      const XfaIconJointStateP* dof_positions, XfaIconMatrix6Nd* jacobian_out);
  // Writes the base to tip transform for the given `dof_positions` into
  // `pose_out`. Assumes the kinematic model is a chain and returns an error
  // otherwise.
  XfaIconRealtimeStatus (*compute_chain_fk)(
      const XfaIconFeatureInterfaceManipulatorKinematics* self,
      const XfaIconJointStateP* dof_positions, XfaIconPose3d* pose_out);
};

// Holds pointers to the feature interfaces for a given Slot. If the Part
// assigned to that Slot does not implement an interface, the corresponding
// member is set to nullptr.
//
struct XfaIconFeatureInterfacesForSlot {
  XfaIconFeatureInterfaceJointPositionCommandInterface* joint_position;
  XfaIconFeatureInterfaceJointPositionSensor* joint_position_sensor;
  XfaIconFeatureInterfaceJointVelocityEstimator* joint_velocity_estimator;
  XfaIconFeatureInterfaceJointLimits* joint_limits;
  XfaIconFeatureInterfaceManipulatorKinematics* manipulator_kinematics;
  XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor;
};

// Same as above, but holds const pointers. This prevents Actions from sending
// commands to a Feature Interface when they should not be able to do so.
struct XfaIconConstFeatureInterfacesForSlot {
  const XfaIconFeatureInterfaceJointPositionCommandInterface* joint_position;
  const XfaIconFeatureInterfaceJointPositionSensor* joint_position_sensor;
  const XfaIconFeatureInterfaceJointVelocityEstimator* joint_velocity_estimator;
  const XfaIconFeatureInterfaceJointLimits* joint_limits;
  const XfaIconFeatureInterfaceManipulatorKinematics* manipulator_kinematics;
  const XfaIconFeatureInterfaceForceTorqueSensor* force_torque_sensor;
};

// Holds function pointers to the functions for each FeatureInterface. Plugin
// code can then call those functions like this
//
// XfaIconFeatureInterfaceVtable feature_interfaces =
//   server_functions.feature_interfaces;
// XfaIconFeatureInterfaceJointPositionCommandInterface*
// joint_position_interface =
//   GetJointPositionCommandInterfaceFromSomewhere();
// XfaIconJointPositionCommand command;
// command.position_setpoints[0]= 1.0;
// command.position_setpoints[1]= 1.5;
// command.position_setpoints[2]= 0.7;
// command.position_setpoints_size = 0;
// command.velocity_feedforwards_size = 0;
// command.acceleration_feedforwards_size = 0;
//
// XfaIconRealtimeStatus result =
// feature_interfaces.joint_position.set_position_setpoints(
//    joint_position_interface, &command);
struct XfaIconFeatureInterfaceVtable {
  XfaIconFeatureInterfaceJointPositionCommandInterfaceVtable joint_position;
  XfaIconFeatureInterfaceJointPositionSensorVtable joint_position_sensor;
  XfaIconFeatureInterfaceJointVelocityEstimatorVtable joint_velocity_estimator;
  XfaIconFeatureInterfaceJointLimitsVtable joint_limits;
  XfaIconFeatureInterfaceManipulatorKinematicsVtable manipulator_kinematics;
  XfaIconFeatureInterfaceForceTorqueSensorVtable force_torque_sensor;
};
#ifdef __cplusplus
}
#endif

#endif  // INTRINSIC_ICON_CONTROL_C_API_C_FEATURE_INTERFACES_H_
