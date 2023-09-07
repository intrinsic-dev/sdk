// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/external_action_api/testing/loopback_fake_arm.h"

#include <optional>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "intrinsic/eigenmath/rotation_utils.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/c_api/c_feature_interfaces.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/control/c_api/c_types.h"
#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"
#include "intrinsic/icon/control/c_api/convert_c_types.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/icon/proto/generic_part_config.pb.h"
#include "intrinsic/icon/utils/realtime_status.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_limits.pb.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic::icon {

// static
absl::StatusOr<::intrinsic_proto::icon::PartConfig>
LoopbackFakeArm::GetPartConfig(absl::string_view name,
                               std::optional<JointLimits> application_limits,
                               std::optional<JointLimits> system_limits) {
  ::intrinsic_proto::icon::PartConfig config;
  config.set_name(std::string(name));
  config.set_part_type_name("loopback_fake_arm");
  ::intrinsic_proto::icon::GenericPartConfig* generic_config =
      config.mutable_generic_config();
  generic_config->mutable_joint_position_config()->set_num_joints(kNdof);
  generic_config->mutable_joint_position_sensor_config()->set_num_joints(kNdof);
  generic_config->mutable_joint_velocity_estimator_config()->set_num_joints(
      kNdof);
  auto unlimited = JointLimits::Unlimited(kNdof);
  if (!unlimited.status().ok()) {
    return unlimited.status();
  }
  *generic_config->mutable_joint_limits_config()->mutable_application_limits() =
      ToProto(application_limits.value_or(unlimited.value()));
  *generic_config->mutable_joint_limits_config()->mutable_system_limits() =
      ToProto(system_limits.value_or(unlimited.value()));
  if (size_t application_limits_size = generic_config->joint_limits_config()
                                           .application_limits()
                                           .min_position()
                                           .values_size();
      application_limits_size != kNdof) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Application limits for LoopbackFakeArm must have 6 DoFs, but got ",
        application_limits_size));
  }
  if (size_t system_limits_size = generic_config->joint_limits_config()
                                      .system_limits()
                                      .min_position()
                                      .values_size();
      system_limits_size != kNdof) {
    return absl::InvalidArgumentError(absl::StrCat(
        "System limits for LoopbackFakeArm must have 6 DoFs, but got ",
        system_limits_size));
  }
  // Touch ManipulatorKinematics field to ensure it is present
  generic_config->mutable_manipulator_kinematics_config();
  return config;
}

// static
XfaIconFeatureInterfaceVtable LoopbackFakeArm::GetFeatureInterfaceVtable() {
  return {
      .joint_position = {
          .set_position_setpoints =
              [](XfaIconFeatureInterfaceJointPositionCommandInterface* self,
                 const XfaIconJointPositionCommand* const setpoints)
              -> XfaIconRealtimeStatus {
            auto arm = reinterpret_cast<LoopbackFakeArm*>(self);
            return FromRealtimeStatus(
                arm->SetPositionSetpoints(Convert(*setpoints)));
          },
          .previous_position_setpoints =
              [](const XfaIconFeatureInterfaceJointPositionCommandInterface*
                     self) -> XfaIconJointPositionCommand {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            return Convert(arm->PreviousPositionSetpoints());
          },
      },
      .joint_position_sensor =
          {
              .get_sensed_position =
                  [](const XfaIconFeatureInterfaceJointPositionSensor* self)
                  -> XfaIconJointStateP {
                auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
                return Convert(arm->GetSensedPosition());
              },
          },
      .joint_velocity_estimator =
          {
              .get_velocity_estimate =
                  [](const XfaIconFeatureInterfaceJointVelocityEstimator* self)
                  -> XfaIconJointStateV {
                auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
                return Convert(arm->GetVelocityEstimate());
              },
          },
      .joint_limits = {
          .get_application_limits =
              [](const XfaIconFeatureInterfaceJointLimits* self)
              -> XfaIconJointLimits {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            return Convert(arm->GetApplicationLimits());
          },
          .get_system_limits =
              [](const XfaIconFeatureInterfaceJointLimits* self)
              -> XfaIconJointLimits {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            return Convert(arm->GetSystemLimits());
          },
      },
      .manipulator_kinematics = {
          .compute_chain_jacobian =
              [](const XfaIconFeatureInterfaceManipulatorKinematics* self,
                 const XfaIconJointStateP* dof_positions,
                 XfaIconMatrix6Nd* jacobian_out) -> XfaIconRealtimeStatus {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            RealtimeStatusOr<eigenmath::Matrix6Nd> jacobian =
                arm->ComputeChainJacobian(Convert(*dof_positions));
            if (!jacobian.ok()) {
              return FromRealtimeStatus(jacobian.status());
            }
            *jacobian_out = Convert(jacobian.value());
            return FromRealtimeStatus(OkStatus());
          },
          .compute_chain_fk =
              [](const XfaIconFeatureInterfaceManipulatorKinematics* self,
                 const XfaIconJointStateP* dof_positions,
                 XfaIconPose3d* pose_out) -> XfaIconRealtimeStatus {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            RealtimeStatusOr<Pose3d> pose =
                arm->ComputeChainFK(Convert(*dof_positions));
            if (!pose.ok()) {
              return FromRealtimeStatus(pose.status());
            }
            *pose_out = Convert(pose.value());
            return FromRealtimeStatus(OkStatus());
          },
      },
      .force_torque_sensor = {
          .wrench_at_tip =
              [](const XfaIconFeatureInterfaceForceTorqueSensor* self)
              -> XfaIconWrench {
            auto arm = reinterpret_cast<const LoopbackFakeArm*>(self);
            return Convert(arm->WrenchAtTip());
          },
          .tare = [](XfaIconFeatureInterfaceForceTorqueSensor* self)
              -> XfaIconRealtimeStatus {
            auto arm = reinterpret_cast<LoopbackFakeArm*>(self);
            return FromRealtimeStatus(arm->Tare());
          },
      },
  };
}

// static
XfaIconFeatureInterfacesForSlot
LoopbackFakeArm::MakeXfaIconFeatureInterfacesForSlot(LoopbackFakeArm* arm) {
  return {
      .joint_position = reinterpret_cast<
          XfaIconFeatureInterfaceJointPositionCommandInterface*>(arm),
      .joint_position_sensor =
          reinterpret_cast<XfaIconFeatureInterfaceJointPositionSensor*>(arm),
      .joint_velocity_estimator =
          reinterpret_cast<XfaIconFeatureInterfaceJointVelocityEstimator*>(arm),
      .joint_limits =
          reinterpret_cast<XfaIconFeatureInterfaceJointLimits*>(arm),
      .manipulator_kinematics =
          reinterpret_cast<XfaIconFeatureInterfaceManipulatorKinematics*>(arm),
      .force_torque_sensor =
          reinterpret_cast<XfaIconFeatureInterfaceForceTorqueSensor*>(arm),
  };
}

// static
XfaIconConstFeatureInterfacesForSlot
LoopbackFakeArm::MakeXfaIconConstFeatureInterfacesForSlot(
    const LoopbackFakeArm* arm) {
  return {
      .joint_position = reinterpret_cast<
          const XfaIconFeatureInterfaceJointPositionCommandInterface*>(arm),
      .joint_position_sensor =
          reinterpret_cast<const XfaIconFeatureInterfaceJointPositionSensor*>(
              arm),
      .joint_velocity_estimator = reinterpret_cast<
          const XfaIconFeatureInterfaceJointVelocityEstimator*>(arm),
      .joint_limits =
          reinterpret_cast<const XfaIconFeatureInterfaceJointLimits*>(arm),
      .manipulator_kinematics =
          reinterpret_cast<const XfaIconFeatureInterfaceManipulatorKinematics*>(
              arm),
      .force_torque_sensor =
          reinterpret_cast<const XfaIconFeatureInterfaceForceTorqueSensor*>(
              arm),
  };
}

LoopbackFakeArm::LoopbackFakeArm()
    : current_setpoints_(
          JointPositionCommand(eigenmath::VectorNd::Zero(kNdof))),
      application_limits_(JointLimits::Unlimited(kNdof).value()),
      system_limits_(JointLimits::Unlimited(kNdof).value()),
      current_wrench_at_tip_(Wrench::ZERO) {}

absl::Status LoopbackFakeArm::SetApplicationLimits(
    const JointLimits& application_limits) {
  if (application_limits.size() != kNdof) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Application limits must have 6 DoF, got ", application_limits.size()));
  }
  application_limits_ = application_limits;
  return absl::OkStatus();
}

absl::Status LoopbackFakeArm::SetSystemLimits(
    const JointLimits& system_limits) {
  if (system_limits.size() != kNdof) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Maximum limits must have 6 DoF, got ", system_limits.size()));
  }
  system_limits_ = system_limits;
  return absl::OkStatus();
}

void LoopbackFakeArm::SetWrenchAtTip(const Wrench& wrench_at_tip) {
  current_wrench_at_tip_ = wrench_at_tip;
}

RealtimeStatus LoopbackFakeArm::SetPositionSetpoints(
    const JointPositionCommand& setpoints) {
  if (setpoints.Size() != kNdof) {
    return InvalidArgumentError(RealtimeStatus::StrCat(
        "Position setpoints must have 6 DoF, got ", setpoints.Size()));
  }
  current_setpoints_ = setpoints;
  return OkStatus();
}

JointPositionCommand LoopbackFakeArm::PreviousPositionSetpoints() const {
  return current_setpoints_;
}

JointStateP LoopbackFakeArm::GetSensedPosition() const {
  JointStateP state_out = JointStateP::Zero(kNdof);
  state_out.position = current_setpoints_.position();
  return state_out;
}

JointStateV LoopbackFakeArm::GetVelocityEstimate() const {
  JointStateV state_out = JointStateV::Zero(kNdof);
  if (!current_setpoints_.velocity_feedforward().has_value()) {
    return state_out;
  }
  state_out.velocity = current_setpoints_.velocity_feedforward().value();
  return state_out;
}

JointLimits LoopbackFakeArm::GetApplicationLimits() const {
  return application_limits_;
}

JointLimits LoopbackFakeArm::GetSystemLimits() const { return system_limits_; }

Wrench LoopbackFakeArm::WrenchAtTip() const { return current_wrench_at_tip_; }

RealtimeStatus LoopbackFakeArm::Tare() {
  current_wrench_at_tip_ = Wrench::ZERO;
  return OkStatus();
}

RealtimeStatusOr<Pose3d> LoopbackFakeArm::ComputeChainFK(
    const JointStateP dof_positions) const {
  if (dof_positions.size() != kNdof) {
    return InvalidArgumentError(RealtimeStatus::StrCat(
        "Position setpoints must have 6 DoF, got ", dof_positions.size()));
  }
  Pose3d pose_out;
  pose_out.translation().x() = dof_positions.position(0);
  pose_out.translation().y() = dof_positions.position(1);
  pose_out.translation().z() = dof_positions.position(2);
  pose_out.setQuaternion(eigenmath::QuaternionFromRPY(
      dof_positions.position(3), dof_positions.position(4),
      dof_positions.position(5)));
  return pose_out;
}

RealtimeStatusOr<eigenmath::Matrix6Nd> LoopbackFakeArm::ComputeChainJacobian(
    const JointStateP dof_positions) const {
  if (dof_positions.size() != kNdof) {
    return InvalidArgumentError(RealtimeStatus::StrCat(
        "Position setpoints must have 6 DoF, got ", dof_positions.size()));
  }
  return {eigenmath::Matrix6Nd::Identity(6, 6)};
}

}  // namespace intrinsic::icon
