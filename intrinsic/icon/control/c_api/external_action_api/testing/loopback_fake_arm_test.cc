// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/external_action_api/testing/loopback_fake_arm.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "absl/status/status.h"
#include "intrinsic/eigenmath/rotation_utils.h"
#include "intrinsic/eigenmath/types.h"
#include "intrinsic/icon/control/c_api/external_action_api/icon_feature_interfaces.h"
#include "intrinsic/icon/control/joint_position_command.h"
#include "intrinsic/icon/proto/generic_part_config.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/utils/realtime_status_matchers.h"
#include "intrinsic/kinematics/types/joint_limits.h"
#include "intrinsic/kinematics/types/joint_state.h"
#include "intrinsic/math/pose3.h"
#include "intrinsic/math/twist.h"

namespace intrinsic::icon {
namespace {

using ::testing::DoubleEq;
using ::testing::Each;
using ::testing::EqualsProto;
using ::testing::Optional;
using ::testing::status::StatusIs;

TEST(LoopbackFakeArm, GetPartConfigRejectsWrongSizedApplicationLimits) {
  JointLimits wrong_size_application_limits = CreateSimpleJointLimits(
      /*ndof=*/2, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);
  JointLimits valid_system_limits = CreateSimpleJointLimits(6, 1, 2, 3, 4);
  EXPECT_THAT(LoopbackFakeArm::GetPartConfig(
                  "the_golden_arm",
                  /*application_limits=*/wrong_size_application_limits,
                  /*system_limits=*/valid_system_limits),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, GetPartConfigRejectsWrongSizedMaximumLimits) {
  JointLimits valid_application_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);
  JointLimits wrong_size_system_limits = CreateSimpleJointLimits(
      /*ndof=*/2, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);
  EXPECT_THAT(
      LoopbackFakeArm::GetPartConfig(
          "the_golden_arm", /*application_limits=*/valid_application_limits,
          /*system_limits=*/wrong_size_system_limits),
      StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, GetPartConfig) {
  JointLimits expected_application_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);
  JointLimits expected_system_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/5, /*max_velocity=*/6,
      /*max_acceleration=*/7, /*max_jerk=*/8);
  ASSERT_OK_AND_ASSIGN(
      ::intrinsic_proto::icon::PartConfig config,
      LoopbackFakeArm::GetPartConfig(
          "the_golden_arm", /*application_limits=*/expected_application_limits,
          /*system_limits=*/expected_system_limits));

  EXPECT_EQ(config.name(), "the_golden_arm");
  ::intrinsic_proto::icon::GenericPartConfig generic_config =
      config.generic_config();

  EXPECT_EQ(generic_config.joint_position_config().num_joints(), 6);
  EXPECT_EQ(generic_config.joint_position_sensor_config().num_joints(), 6);
  EXPECT_EQ(generic_config.joint_velocity_estimator_config().num_joints(), 6);
  EXPECT_THAT(generic_config.joint_limits_config().application_limits(),
              EqualsProto(ToProto(expected_application_limits)));
  EXPECT_THAT(generic_config.joint_limits_config().system_limits(),
              EqualsProto(ToProto(expected_system_limits)));
  EXPECT_TRUE(generic_config.has_manipulator_kinematics_config());
}

TEST(LoopbackFakeArm, GetPartConfigDefaultsToUnlimitedJointLImits) {
  ASSERT_OK_AND_ASSIGN(::intrinsic_proto::icon::PartConfig config,
                       LoopbackFakeArm::GetPartConfig("the_golden_arm"));

  ::intrinsic_proto::icon::GenericPartConfig generic_config =
      config.generic_config();

  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(auto expected_limits,
                                    JointLimits::Unlimited(6));
  EXPECT_THAT(generic_config.joint_limits_config().application_limits(),
              EqualsProto(ToProto(expected_limits)));
  EXPECT_THAT(generic_config.joint_limits_config().system_limits(),
              EqualsProto(ToProto(expected_limits)));
}

TEST(LoopbackFakeArm, MakeXfaIconConstFeatureInterfacesForSlot) {
  LoopbackFakeArm arm;
  auto feature_interfaces =
      LoopbackFakeArm::MakeXfaIconConstFeatureInterfacesForSlot(&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_position, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_position_sensor, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_velocity_estimator, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_limits, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.manipulator_kinematics, (void*)&arm);
}

TEST(LoopbackFakeArm, MakeXfaIconFeatureInterfacesForSlot) {
  LoopbackFakeArm arm;
  auto feature_interfaces =
      LoopbackFakeArm::MakeXfaIconFeatureInterfacesForSlot(&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_position, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_position_sensor, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_velocity_estimator, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.joint_limits, (void*)&arm);
  EXPECT_EQ((void*)feature_interfaces.manipulator_kinematics, (void*)&arm);
}

TEST(LoopbackFakeArm, PositionAndVelocityStartAtZero) {
  LoopbackFakeArm arm;
  JointPositionCommand initial_command = arm.PreviousPositionSetpoints();

  EXPECT_TRUE(initial_command.position().isZero());
  EXPECT_FALSE(initial_command.velocity_feedforward().has_value());
  EXPECT_FALSE(initial_command.acceleration_feedforward().has_value());
  EXPECT_TRUE(arm.GetSensedPosition().position.isZero());
  EXPECT_TRUE(arm.GetVelocityEstimate().velocity.isZero());
}

TEST(LoopbackFakeArm, WrenchStartsAtZero) {
  EXPECT_TRUE(LoopbackFakeArm().WrenchAtTip().isZero());
}

TEST(LoopbackFakeArm, LimitsStartUnlimited) {
  LoopbackFakeArm arm;

  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(auto expected_limits,
                                    JointLimits::Unlimited(6));
  EXPECT_THAT(ToProto(arm.GetApplicationLimits()),
              EqualsProto(ToProto(expected_limits)));
  EXPECT_THAT(ToProto(arm.GetSystemLimits()),
              EqualsProto(ToProto(expected_limits)));
}

TEST(LoopbackFakeArm, RejectsPositionCommandWithWrongSize) {
  EXPECT_THAT(LoopbackFakeArm().SetPositionSetpoints(
                  JointPositionCommand(eigenmath::VectorNd::Constant(1, 1))),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, EchoesPositionCommand) {
  LoopbackFakeArm arm;
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      auto initial_setpoints,
      JointPositionCommand::Create(
          /*position=*/eigenmath::VectorNd::Constant(6, 1),
          /*velocity_feedforward=*/eigenmath::VectorNd::Constant(6, 2),
          /*acceleration_feedforward=*/eigenmath::VectorNd::Constant(6, 3)));
  EXPECT_OK(arm.SetPositionSetpoints(initial_setpoints));

  JointPositionCommand initial_command_read = arm.PreviousPositionSetpoints();
  JointStateP initial_position = arm.GetSensedPosition();
  JointStateV initial_velocity = arm.GetVelocityEstimate();
  EXPECT_THAT(initial_command_read.position(), Each(DoubleEq(1)));
  EXPECT_THAT(initial_command_read.velocity_feedforward(),
              Optional(Each(DoubleEq(2))));
  EXPECT_THAT(initial_command_read.acceleration_feedforward(),
              Optional(Each(DoubleEq(3))));
  EXPECT_THAT(initial_position.position, Each(DoubleEq(1)));
  EXPECT_THAT(initial_velocity.velocity, Each(DoubleEq(2)));
}

TEST(LoopbackFakeArm, EchoesWrench) {
  LoopbackFakeArm arm;
  Wrench expected_wrench(/*x=*/1, /*y=*/2, /*z=*/3, /*RX=*/4, /*RY=*/5,
                         /*RZ=*/6);
  arm.SetWrenchAtTip(expected_wrench);
  EXPECT_EQ(arm.WrenchAtTip(), expected_wrench);
}

TEST(LoopbackFakeArm, TareResetsWrench) {
  LoopbackFakeArm arm;
  arm.SetWrenchAtTip(Wrench(/*x=*/1, /*y=*/2, /*z=*/3, /*RX=*/4, /*RY=*/5,
                            /*RZ=*/6));
  EXPECT_OK(arm.Tare());
  EXPECT_EQ(arm.WrenchAtTip(), Wrench::ZERO);
}

TEST(LoopbackFakeArm, RejectsDefaultLimitsWithWrongSize) {
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(auto limits_wrong_size,
                                    JointLimits::Unlimited(1));
  EXPECT_THAT(LoopbackFakeArm().SetApplicationLimits(limits_wrong_size),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, EchoesDefaultLimits) {
  LoopbackFakeArm arm;
  JointLimits expected_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);

  EXPECT_OK(arm.SetApplicationLimits(expected_limits));
  EXPECT_THAT(ToProto(arm.GetApplicationLimits()),
              EqualsProto(ToProto(expected_limits)));
}

TEST(LoopbackFakeArm, RejectsMaximumLimitsWithWrongSize) {
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(auto limits_wrong_size,
                                    JointLimits::Unlimited(1));
  EXPECT_THAT(LoopbackFakeArm().SetSystemLimits(limits_wrong_size),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, EchoesMaximumLimits) {
  LoopbackFakeArm arm;
  JointLimits expected_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);

  EXPECT_OK(arm.SetSystemLimits(expected_limits));
  EXPECT_THAT(ToProto(arm.GetSystemLimits()),
              EqualsProto(ToProto(expected_limits)));
}

TEST(LoopbackFakeArm, ComputeJacobianRejectsWrongSize) {
  EXPECT_THAT(
      LoopbackFakeArm().ComputeChainJacobian(JointStateP::Zero(1)).status(),
      StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, JacobianIsIdentity) {
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      eigenmath::Matrix6Nd jacobian,
      LoopbackFakeArm().ComputeChainJacobian(JointStateP::Zero(6)));
  EXPECT_TRUE(jacobian.isIdentity());
}

TEST(LoopbackFakeArm, ComputeChainFKRejectsWrongSize) {
  EXPECT_THAT(LoopbackFakeArm().ComputeChainFK(JointStateP::Zero(1)).status(),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST(LoopbackFakeArm, ChainFKReturnsIdentity) {
  JointStateP input_position;
  ASSERT_OK(input_position.SetSize(6));
  input_position.position << 1, 2, 3, 4, 5, 6;
  eigenmath::Quaterniond expected_quaternion =
      eigenmath::QuaternionFromRPY(4., 5., 6.);
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      Pose3d fk_pose, LoopbackFakeArm().ComputeChainFK(input_position));
  EXPECT_EQ(fk_pose.translation().x(), 1);
  EXPECT_EQ(fk_pose.translation().y(), 2);
  EXPECT_EQ(fk_pose.translation().z(), 3);
  EXPECT_EQ(fk_pose.quaternion().x(), expected_quaternion.x());
  EXPECT_EQ(fk_pose.quaternion().y(), expected_quaternion.y());
  EXPECT_EQ(fk_pose.quaternion().z(), expected_quaternion.z());
  EXPECT_EQ(fk_pose.quaternion().w(), expected_quaternion.w());
}

TEST(LoopbackFakeArm, FeatureInterfacePointersNotNull) {
  LoopbackFakeArm arm;
  auto feature_interfaces =
      LoopbackFakeArm::MakeXfaIconFeatureInterfacesForSlot(&arm);
  EXPECT_NE(feature_interfaces.joint_position, nullptr);
  EXPECT_NE(feature_interfaces.joint_position_sensor, nullptr);
  EXPECT_NE(feature_interfaces.joint_velocity_estimator, nullptr);
  EXPECT_NE(feature_interfaces.manipulator_kinematics, nullptr);
}

class LoopbackFakeArmIconFeatureInterfaces : public ::testing::Test {
 public:
  LoopbackFakeArmIconFeatureInterfaces()
      : arm_(),
        feature_interfaces_(FromCApiFeatureInterfaces(
            LoopbackFakeArm::MakeXfaIconFeatureInterfacesForSlot(&arm_),
            LoopbackFakeArm::GetFeatureInterfaceVtable())),
        const_feature_interfaces_(FromCApiFeatureInterfaces(
            LoopbackFakeArm::MakeXfaIconConstFeatureInterfacesForSlot(&arm_),
            LoopbackFakeArm::GetFeatureInterfaceVtable())) {}

 protected:
  LoopbackFakeArm arm_;
  IconFeatureInterfaces feature_interfaces_;
  const IconConstFeatureInterfaces const_feature_interfaces_;
};

TEST_F(LoopbackFakeArmIconFeatureInterfaces, AllFeatureInterfacesPresent) {
  EXPECT_TRUE(feature_interfaces_.joint_position.has_value());
  EXPECT_TRUE(feature_interfaces_.joint_position_sensor.has_value());
  EXPECT_TRUE(feature_interfaces_.joint_velocity_estimator.has_value());
  EXPECT_TRUE(feature_interfaces_.joint_limits.has_value());
  EXPECT_TRUE(feature_interfaces_.force_torque_sensor.has_value());
  EXPECT_TRUE(feature_interfaces_.manipulator_kinematics.has_value());
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, AllConstFeatureInterfacesPresent) {
  EXPECT_TRUE(const_feature_interfaces_.joint_position.has_value());
  EXPECT_TRUE(const_feature_interfaces_.joint_position_sensor.has_value());
  EXPECT_TRUE(const_feature_interfaces_.joint_velocity_estimator.has_value());
  EXPECT_TRUE(const_feature_interfaces_.joint_limits.has_value());
  EXPECT_TRUE(const_feature_interfaces_.force_torque_sensor.has_value());
  EXPECT_TRUE(const_feature_interfaces_.manipulator_kinematics.has_value());
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, EchoesJointPositionCommand) {
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      JointPositionCommand expected_command,
      JointPositionCommand::Create(
          /*position=*/eigenmath::VectorNd::Constant(6, 1),
          /*velocity_feedforward=*/eigenmath::VectorNd::Constant(6, 2),
          /*acceleration_feedforward=*/eigenmath::VectorNd::Constant(6, 3)));
  EXPECT_OK(feature_interfaces_.joint_position->SetPositionSetpoints(
      expected_command));
  JointPositionCommand previous_command =
      feature_interfaces_.joint_position->PreviousPositionSetpoints();
  EXPECT_THAT(previous_command.position(), Each(1));
  EXPECT_THAT(previous_command.velocity_feedforward(), Optional(Each(2)));
  EXPECT_THAT(previous_command.acceleration_feedforward(), Optional(Each(3)));
  EXPECT_THAT(
      feature_interfaces_.joint_position_sensor->GetSensedPosition().position,
      Each(1));
  EXPECT_THAT(
      feature_interfaces_.joint_velocity_estimator->GetVelocityEstimate()
          .velocity,
      Each(2));

  // The const feature interfaces should report the same values
  JointPositionCommand previous_command_from_const_interface =
      const_feature_interfaces_.joint_position->PreviousPositionSetpoints();
  EXPECT_THAT(previous_command_from_const_interface.position(), Each(1));
  EXPECT_THAT(previous_command_from_const_interface.velocity_feedforward(),
              Optional(Each(2)));
  EXPECT_THAT(previous_command_from_const_interface.acceleration_feedforward(),
              Optional(Each(3)));
  EXPECT_THAT(
      const_feature_interfaces_.joint_position_sensor->GetSensedPosition()
          .position,
      Each(1));
  EXPECT_THAT(
      const_feature_interfaces_.joint_velocity_estimator->GetVelocityEstimate()
          .velocity,
      Each(2));
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, ReportsLimits) {
  JointLimits expected_application_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/1, /*max_velocity=*/2,
      /*max_acceleration=*/3, /*max_jerk=*/4);
  EXPECT_OK(arm_.SetApplicationLimits(expected_application_limits));
  JointLimits expected_system_limits = CreateSimpleJointLimits(
      /*ndof=*/6, /*max_position=*/5, /*max_velocity=*/6,
      /*max_acceleration=*/7, /*max_jerk=*/8);
  EXPECT_OK(arm_.SetSystemLimits(expected_system_limits));

  EXPECT_THAT(ToProto(feature_interfaces_.joint_limits->GetApplicationLimits()),
              EqualsProto(ToProto(expected_application_limits)));
  EXPECT_THAT(ToProto(feature_interfaces_.joint_limits->GetSystemLimits()),
              EqualsProto(ToProto(expected_system_limits)));

  EXPECT_THAT(
      ToProto(const_feature_interfaces_.joint_limits->GetApplicationLimits()),
      EqualsProto(ToProto(expected_application_limits)));
  EXPECT_THAT(
      ToProto(const_feature_interfaces_.joint_limits->GetSystemLimits()),
      EqualsProto(ToProto(expected_system_limits)));
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, ComputeFKRejectsWrongSize) {
  EXPECT_THAT(feature_interfaces_.manipulator_kinematics
                  ->ComputeChainFK(JointStateP::Zero(2))
                  .status(),
              StatusIs(absl::StatusCode::kInvalidArgument));
  EXPECT_THAT(const_feature_interfaces_.manipulator_kinematics
                  ->ComputeChainFK(JointStateP::Zero(2))
                  .status(),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, ComputeFK) {
  JointStateP input_position;
  ASSERT_OK(input_position.SetSize(6));
  input_position.position << 1, 2, 3, 4, 5, 6;
  eigenmath::Quaterniond expected_quaternion =
      eigenmath::QuaternionFromRPY(4., 5., 6.);
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      Pose3d fk_pose,
      feature_interfaces_.manipulator_kinematics->ComputeChainFK(
          input_position));
  EXPECT_EQ(fk_pose.translation().x(), 1);
  EXPECT_EQ(fk_pose.translation().y(), 2);
  EXPECT_EQ(fk_pose.translation().z(), 3);
  EXPECT_EQ(fk_pose.quaternion().x(), expected_quaternion.x());
  EXPECT_EQ(fk_pose.quaternion().y(), expected_quaternion.y());
  EXPECT_EQ(fk_pose.quaternion().z(), expected_quaternion.z());
  EXPECT_EQ(fk_pose.quaternion().w(), expected_quaternion.w());

  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      Pose3d const_fk_pose,
      const_feature_interfaces_.manipulator_kinematics->ComputeChainFK(
          input_position));
  EXPECT_EQ(const_fk_pose.translation().x(), 1);
  EXPECT_EQ(const_fk_pose.translation().y(), 2);
  EXPECT_EQ(const_fk_pose.translation().z(), 3);
  EXPECT_EQ(const_fk_pose.quaternion().x(), expected_quaternion.x());
  EXPECT_EQ(const_fk_pose.quaternion().y(), expected_quaternion.y());
  EXPECT_EQ(const_fk_pose.quaternion().z(), expected_quaternion.z());
  EXPECT_EQ(const_fk_pose.quaternion().w(), expected_quaternion.w());
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, ComputeJacobianRejectsWrongSize) {
  EXPECT_THAT(feature_interfaces_.manipulator_kinematics
                  ->ComputeChainJacobian(JointStateP::Zero(2))
                  .status(),
              StatusIs(absl::StatusCode::kInvalidArgument));
  EXPECT_THAT(const_feature_interfaces_.manipulator_kinematics
                  ->ComputeChainJacobian(JointStateP::Zero(2))
                  .status(),
              StatusIs(absl::StatusCode::kInvalidArgument));
}

TEST_F(LoopbackFakeArmIconFeatureInterfaces, ComputeJacobian) {
  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      eigenmath::Matrix6Nd jacobian,
      feature_interfaces_.manipulator_kinematics->ComputeChainJacobian(
          JointStateP::Zero(6)));
  EXPECT_TRUE(jacobian.isIdentity());

  INTRINSIC_RT_ASSERT_OK_AND_ASSIGN(
      eigenmath::Matrix6Nd const_jacobian,
      const_feature_interfaces_.manipulator_kinematics->ComputeChainJacobian(
          JointStateP::Zero(6)));
  EXPECT_TRUE(const_jacobian.isIdentity());
}

}  // namespace
}  // namespace intrinsic::icon
