// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/convert_c_types.h"

#include <cstring>
#include <optional>

#include "Eigen/Core"
#include "absl/log/log.h"
#include "absl/types/optional.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/c_api/c_types.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"

namespace intrinsic::icon {
namespace {
static_assert(
    kXfaIconMaxNumberOfJoints == eigenmath::MAX_EIGEN_VECTOR_SIZE,
    "Mismatch between maximum size of C++ (intrinsic::eigenmath) and C "
    "vectors. This breaks the ICON C API!");
}

JointPositionCommand Convert(const XfaIconJointPositionCommand& in) {
  CHECK(in.size < kXfaIconMaxNumberOfJoints)
      << "XfaIconJointPositionCommand has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  eigenmath::VectorNd position_setpoints(
      Eigen::Map<const eigenmath::VectorNd>(in.position_setpoints, in.size));
  // Return .value() without checking because we guarantee that position,
  // velocity and acceleration are the same size here.
  return JointPositionCommand::Create(
             Eigen::Map<const eigenmath::VectorNd>(in.position_setpoints,
                                                   in.size),
             in.has_velocity_feedforwards
                 ? std::make_optional(eigenmath::VectorNd(
                       Eigen::Map<const eigenmath::VectorNd>(
                           in.velocity_feedforwards, in.size)))
                 : std::nullopt,
             in.has_acceleration_feedforwards
                 ? std::make_optional(eigenmath::VectorNd(
                       Eigen::Map<const eigenmath::VectorNd>(
                           in.acceleration_feedforwards, in.size)))
                 : std::nullopt)
      .value();
}

XfaIconJointPositionCommand Convert(const JointPositionCommand& in) {
  CHECK(in.Size() < kXfaIconMaxNumberOfJoints)
      << "JointPositionCommand has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  XfaIconJointPositionCommand out{.size = in.Size()};
  for (size_t i = 0; i < out.size; ++i) {
    out.position_setpoints[i] = in.position()(i);
    if (in.velocity_feedforward().has_value()) {
      out.has_velocity_feedforwards = true;
      out.velocity_feedforwards[i] = in.velocity_feedforward().value()(i);
    }
    if (in.acceleration_feedforward().has_value()) {
      out.has_acceleration_feedforwards = true;
      out.acceleration_feedforwards[i] =
          in.acceleration_feedforward().value()(i);
    }
  }
  return out;
}

JointLimits Convert(const XfaIconJointLimits& in) {
  CHECK(in.size < kXfaIconMaxNumberOfJoints)
      << "XfaIconJointLimits has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  return {
      .min_position =
          Eigen::Map<const eigenmath::VectorNd>(in.min_position, in.size),
      .max_position =
          Eigen::Map<const eigenmath::VectorNd>(in.max_position, in.size),
      .max_velocity =
          Eigen::Map<const eigenmath::VectorNd>(in.max_velocity, in.size),
      .max_acceleration =
          Eigen::Map<const eigenmath::VectorNd>(in.max_acceleration, in.size),
      .max_jerk = Eigen::Map<const eigenmath::VectorNd>(in.max_jerk, in.size),
      .max_torque =
          Eigen::Map<const eigenmath::VectorNd>(in.max_torque, in.size),
  };
}

XfaIconJointLimits Convert(const JointLimits& in) {
  CHECK(in.size() < kXfaIconMaxNumberOfJoints)
      << "JointLimits have more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  XfaIconJointLimits out{.size = static_cast<size_t>(in.size())};
  for (size_t i = 0; i < out.size; ++i) {
    out.min_position[i] = in.min_position(i);
    out.max_position[i] = in.max_position(i);
    out.max_velocity[i] = in.max_velocity(i);
    out.max_acceleration[i] = in.max_acceleration(i);
    out.max_jerk[i] = in.max_jerk(i);
    out.max_torque[i] = in.max_torque(i);
  }
  return out;
}

JointStateP Convert(const XfaIconJointStateP& in) {
  CHECK(in.size < kXfaIconMaxNumberOfJoints)
      << "XfaIconJointStateP has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  return JointStateP(
      Eigen::Map<const eigenmath::VectorNd>(in.positions, in.size));
}

XfaIconJointStateP Convert(const JointStateP& in) {
  CHECK(in.size() < kXfaIconMaxNumberOfJoints)
      << "JointStateP has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  XfaIconJointStateP out{.size = static_cast<size_t>(in.size())};
  for (size_t i = 0; i < out.size; ++i) {
    out.positions[i] = in.position(i);
  }
  return out;
}

JointStateV Convert(const XfaIconJointStateV& in) {
  CHECK(in.size < kXfaIconMaxNumberOfJoints)
      << "XfaIconJointStateV has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  return JointStateV(
      Eigen::Map<const eigenmath::VectorNd>(in.velocities, in.size));
}

XfaIconJointStateV Convert(const JointStateV& in) {
  CHECK(in.size() < kXfaIconMaxNumberOfJoints)
      << "JointStateV has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  XfaIconJointStateV out{.size = static_cast<size_t>(in.size())};
  for (size_t i = 0; i < out.size; ++i) {
    out.velocities[i] = in.velocity(i);
  }
  return out;
}

JointStateA Convert(const XfaIconJointStateA& in) {
  CHECK(in.size < kXfaIconMaxNumberOfJoints)
      << "XfaIconJointStateA has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  return JointStateA(
      Eigen::Map<const eigenmath::VectorNd>(in.accelerations, in.size));
}

XfaIconJointStateA Convert(const JointStateA& in) {
  CHECK(in.size() < kXfaIconMaxNumberOfJoints)
      << "JointStateA has more than the maximum of "
      << kXfaIconMaxNumberOfJoints << " joints.";
  XfaIconJointStateA out{.size = static_cast<size_t>(in.size())};
  for (size_t i = 0; i < out.size; ++i) {
    out.accelerations[i] = in.acceleration(i);
  }

  return out;
}

eigenmath::Quaterniond Convert(const XfaIconQuaternion& in) {
  return eigenmath::Quaterniond(/*w=*/in.w, /*x=*/in.x,
                                /*y=*/in.y, /*z=*/in.z);
}

XfaIconQuaternion Convert(const eigenmath::Quaterniond& in) {
  return {.w = in.w(), .x = in.x(), .y = in.y(), .z = in.z()};
}

eigenmath::Vector3d Convert(const XfaIconPoint& in) {
  return eigenmath::Vector3d(/*x=*/in.x, /*y=*/in.y, /*z=*/in.z);
}

XfaIconPoint Convert(const eigenmath::Vector3d& in) {
  return {.x = in.x(), .y = in.y(), .z = in.z()};
}

Pose3d Convert(const XfaIconPose3d& in) {
  return Pose3d(/*rotation=*/Convert(in.rotation),
                /*translation=*/Convert(in.translation));
}

XfaIconPose3d Convert(const Pose3d& in) {
  return {.rotation = Convert(in.quaternion()),
          .translation = Convert(in.translation())};
}

Wrench Convert(const XfaIconWrench& in) {
  return {
      in.x, in.y, in.z, in.rx, in.ry, in.rz,
  };
}

XfaIconWrench Convert(const Wrench& in) {
  return {
      .x = in.x(),
      .y = in.y(),
      .z = in.z(),
      .rx = in.RX(),
      .ry = in.RY(),
      .rz = in.RZ(),
  };
}

eigenmath::Matrix6Nd Convert(const XfaIconMatrix6Nd& in) {
  return Eigen::Map<const eigenmath::Matrix6Nd>(in.data, 6, in.num_cols);
}

XfaIconMatrix6Nd Convert(const eigenmath::Matrix6Nd& in) {
  XfaIconMatrix6Nd out;
  out.num_cols = in.cols();
  std::memcpy(out.data, in.data(), in.size() * sizeof(double));
  return out;
}

}  // namespace intrinsic::icon
