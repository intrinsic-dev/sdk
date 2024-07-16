// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_CONTROL_PARTS_FEATURE_INTERFACES_H_
#define INTRINSIC_ICON_CONTROL_PARTS_FEATURE_INTERFACES_H_

#include <stddef.h>

#include <optional>
#include <string>
#include <string_view>

#include "absl/strings/string_view.h"
#include "absl/types/optional.h"
#include "absl/types/span.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/icon/utils/realtime_status_or.h"
#include "intrinsic/kinematics/types/cartesian_limits.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"
#include "intrinsic/util/fixed_vector.h"

namespace intrinsic::icon {

// These are the FeatureInterfaces that the RTCL supports.
// They are made available to Actions via a Part's FeatureInterfaceRegistry.

class JointPosition {
 public:
  virtual ~JointPosition() = default;
  // Sends the given position setpoints with velocity and torque feedforward
  // values.
  //
  // Returns an error if the setpoints are invalid, i.e. they contain the wrong
  // number of values or violate any limits. Returns an error if the part is
  // currently not in position mode.
  virtual RealtimeStatus SetPositionSetpoints(
      const JointPositionCommand& setpoints) = 0;

  // Returns the setpoints from the previous tick.
  virtual JointPositionCommand PreviousPositionSetpoints() const = 0;
};

class JointVelocity {
 public:
  virtual ~JointVelocity() = default;
  // Sends the given velocity setpoints.
  // Returns an error if the setpoints are invalid, i.e. they contain the wrong
  // number of values or violate any limits.
  // Returns an error if the part is currently not in velocity mode.
  virtual RealtimeStatus SetVelocitySetpoints(
      const eigenmath::VectorNd& setpoints) = 0;
};

class JointPositionSensor {
 public:
  virtual ~JointPositionSensor() = default;
  // Returns sensed position of all joints for this part.
  virtual JointStateP GetSensedPosition() const = 0;
};

class JointVelocityEstimator {
 public:
  virtual ~JointVelocityEstimator() = default;
  // Returns a velocity estimate of all joints for this part.
  virtual JointStateV GetVelocityEstimate() const = 0;
};

class JointAccelerationEstimator {
 public:
  virtual ~JointAccelerationEstimator() = default;
  // Returns a acceleration estimate of all joints for this part.
  virtual JointStateA GetAccelerationEstimate() const = 0;
};

class JointLimitsInterface {
 public:
  virtual ~JointLimitsInterface() = default;
  // Returns the application limits for the joints of this part for the
  // currently active ModeOfSafeOperation. These are configured, for instance
  // for a workcell. Actions should use these joint limits by default and reject
  // any user commands that exceed them.
  //
  // That said, an Action may exploit the margin between application limits and
  // system limits (see below) to better realize a user command. For example, a
  // small overshoot in jerk is acceptable, if it allows achieving velocity or
  // acceleration closer to what the user requested.
  //
  // Values of +/- std::numeric_limits<double>::infinity() designate
  // "unlimited".
  virtual JointLimits GetApplicationLimits() const = 0;

  // Returns the system limits for the joints of this part for the currently
  // active ModeOfSafeOperation.
  // These are hard limits as reported by the hardware itself, and ICON *must
  // not* exceed them. If any Action commands motion outside of the system
  // limits, ICON will terminate that Action immediately, and fault the robot.
  // Values of +/- std::numeric_limits<double>::infinity() designate
  // "unlimited".
  virtual JointLimits GetSystemLimits() const = 0;

  // Returns dynamics-based acceleration limits if joint position/velocity and
  // rigid body dynamics data are available, nullopt otherwise. These limits are
  // centrally computed to avoid its repeated computation in multiple places, as
  // it is computationally expensive to obtain them. It takes around 10 usec.
  struct JointAccelerationLimitsFromDynamics {
    eigenmath::VectorNd joint_acceleration_limits_at_min_torque;
    eigenmath::VectorNd joint_acceleration_limits_at_max_torque;
  };
  virtual icon::RealtimeStatusOr<
      std::optional<JointLimitsInterface::JointAccelerationLimitsFromDynamics>>
  GetJointAccelerationLimitsFromDynamics() const = 0;
};

class CartesianLimitsInterface {
 public:
  virtual ~CartesianLimitsInterface() = default;
  // Returns the default limits for the cartesian degrees of freedom for this
  // part for the currently active ModeOfSafeOperation. These are configured,
  // for instance for a workcell. Actions should use these cartesian limits by
  // default.
  virtual CartesianLimits GetDefaultCartesianLimits() const = 0;
};
// An Inertial Measurement Unit (acceleration sensor).
class InertialMeasurementUnit {
 public:
  virtual ~InertialMeasurementUnit() = default;

  // The sensed linear acceleration.
  virtual eigenmath::Vector3d GetSensedLinearAcceleration() const = 0;

  // The sensed angular velocity.
  virtual eigenmath::Vector3d GetSensedAngularVelocity() const = 0;

  // The sensed orientation as quaternion.
  virtual eigenmath::Quaterniond GetSensedOrientation() const = 0;

  // The transform between robot flange and sensor.
  virtual Pose3d GetPoseInFlangeFrame() const = 0;
};

// Interface for rigid-body manipulator kinematics. The intended implementation
// of this interface is to also keep track of the kinematic chains inside this
// class to access them in real-time code. Assumed there is one ModelInterface
// with multiple tips, chain extraction is not real-time safe, thus all possible
// chains from the single base are built here and stored for later usage.
class ManipulatorKinematics {
 public:
  virtual ~ManipulatorKinematics() = default;
  // Returns the base to tip transform for the given `dof_positions`. Assumes
  // the kinematic model is a chain and returns an error otherwise.
  virtual intrinsic::icon::RealtimeStatusOr<Pose3d> ComputeChainFK(
      const JointStateP& dof_positions) const = 0;
  // Returns the base to tip jacobian for the given `dof_positions`. Assumes
  // the kinematic model is a chain and returns an error otherwise.
  virtual intrinsic::icon::RealtimeStatusOr<eigenmath::Matrix6Nd>
  ComputeChainJacobian(const JointStateP& dof_positions) const = 0;
};

class JointTorque {
 public:
  virtual ~JointTorque() = default;
  // Sends the given torque setpoints.
  // Returns an error if the setpoints are invalid, i.e. they contain the wrong
  // number of values or violate any limits. Note that the Part may not be able
  // to predict position/velocity/acceleration limit violations that the new
  // torque setpoints might cause.
  // Returns an error if the part is currently not in torque mode.
  virtual RealtimeStatus SetTorqueSetpoints(
      const eigenmath::VectorNd& setpoints) = 0;
};

class JointTorqueSensor {
 public:
  virtual ~JointTorqueSensor() = default;
  // Returns sensed torque of all joints for this part.
  virtual JointStateT GetSensedTorque() const = 0;
};
}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_PARTS_FEATURE_INTERFACES_H_
