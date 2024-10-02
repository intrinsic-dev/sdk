// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/testing/skill_test_utils.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>
#include <string>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/time/time.h"
#include "grpcpp/support/status.h"
#include "intrinsic/assets/id_utils.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/motion_planning/motion_planner_client.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.pb.h"
#include "intrinsic/motion_planning/proto/motion_planner_service_mock.grpc.pb.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/cc/skill_logging_context.h"
#include "intrinsic/skills/proto/skill_manifest.pb.h"
#include "intrinsic/skills/testing/echo_skill.h"
#include "intrinsic/skills/testing/echo_skill.pb.h"
#include "intrinsic/util/testing/gtest_wrapper.h"
#include "intrinsic/world/objects/object_world_client.h"
#include "intrinsic/world/proto/object_world_service_mock.grpc.pb.h"

namespace intrinsic {
namespace skills {
namespace {

using ::absl_testing::StatusIs;
using ::testing::_;
using ::testing::HasSubstr;
using ::testing::Return;

TEST(ExecuteSkillTest, ExecuteSkillCallsExecute) {
  auto skill_test_factory = SkillTestFactory();
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
  EchoSkill skill;
  std::unique_ptr<ExecuteContext> context =
      skill_test_factory.MakeExecuteContext({});

  intrinsic_proto::skills::EchoSkillReturn result;
  ASSERT_THAT(ExecuteSkill(skill, request, *context, &result),
              ::absl_testing::IsOk());

  EXPECT_EQ(result.foo(), "foo");
}

TEST(ExecuteSkillTest, ExecuteSkillNoResult) {
  auto skill_test_factory = SkillTestFactory();
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
  EchoSkill skill;
  std::unique_ptr<ExecuteContext> context =
      skill_test_factory.MakeExecuteContext({});

  intrinsic_proto::skills::EchoSkillReturn result;
  ASSERT_THAT(ExecuteSkill(skill, request, *context), ::absl_testing::IsOk());
}

TEST(ExecuteSkillTest, WrongResultTypeReturnsError) {
  auto skill_test_factory = SkillTestFactory();
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
  EchoSkill skill;
  std::unique_ptr<ExecuteContext> context =
      skill_test_factory.MakeExecuteContext({});
  intrinsic_proto::skills::EchoSkillReturn result;

  intrinsic_proto::skills::EchoSkillParams bad_result;
  EXPECT_THAT(ExecuteSkill(skill, request, *context, &bad_result),
              StatusIs(absl::StatusCode::kInvalidArgument,
                       HasSubstr("Skill returned result of type")));
}

TEST(PreviewSkillTest, PreviewSkillCallsPreview) {
  auto skill_test_factory = SkillTestFactory();
  EchoSkill skill;
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  PreviewRequest request = skill_test_factory.MakePreviewRequest(params);
  std::unique_ptr<PreviewContext> context =
      skill_test_factory.MakePreviewContext({});

  intrinsic_proto::skills::EchoSkillReturn result;
  ASSERT_THAT(PreviewSkill(skill, request, *context, &result),
              ::absl_testing::IsOk());

  EXPECT_EQ(result.foo(), "foo");
}

TEST(PreviewSkillTest, PreviewSkillNoResult) {
  auto skill_test_factory = SkillTestFactory();
  EchoSkill skill;
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  PreviewRequest request = skill_test_factory.MakePreviewRequest(params);
  std::unique_ptr<PreviewContext> context =
      skill_test_factory.MakePreviewContext({});

  ASSERT_THAT(PreviewSkill(skill, request, *context), ::absl_testing::IsOk());
}

TEST(PreviewSkillTest, WrongResultTypeReturnsError) {
  auto skill_test_factory = SkillTestFactory();
  EchoSkill skill;
  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  PreviewRequest request = skill_test_factory.MakePreviewRequest(params);
  std::unique_ptr<PreviewContext> context =
      skill_test_factory.MakePreviewContext({});

  intrinsic_proto::skills::EchoSkillParams bad_result;
  EXPECT_THAT(PreviewSkill(skill, request, *context, &bad_result),
              StatusIs(absl::StatusCode::kInvalidArgument,
                       HasSubstr("Skill returned result of type")));
}

using intrinsic_proto::motion_planning::MockMotionPlannerServiceStub;
using intrinsic_proto::world::MockObjectWorldServiceStub;

TEST(SkillTestFactory, MakeExecuteContextProvideAlmostEverything) {
  auto canceller =
      std::make_shared<SkillCancellationManager>(absl::ZeroDuration());
  auto equipment_pack = EquipmentPack();
  ASSERT_TRUE(equipment_pack.Add("foo", {}).ok());
  auto logging_context = SkillLoggingContext{
      .skill_id = "bar",
  };
  auto motion_planner_service =
      std::make_shared<MockMotionPlannerServiceStub>();
  auto object_world_service = std::make_shared<MockObjectWorldServiceStub>();

  auto skill_test_factory = SkillTestFactory();

  auto context = skill_test_factory.MakeExecuteContext({
      .canceller = canceller.get(),
      .equipment_pack = equipment_pack,
      .logging_context = logging_context,
      .motion_planner_service = motion_planner_service,
      .object_world_service = object_world_service,
  });

  EXPECT_EQ(&context->canceller(), canceller.get());
  EXPECT_TRUE(equipment_pack.GetHandle("foo").ok());
  EXPECT_EQ(context->logging_context().skill_id, "bar");
  EXPECT_CALL(*motion_planner_service, ClearCache(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->motion_planner().ClearCache().ok());
  EXPECT_CALL(*object_world_service, ListObjects(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->object_world().ListObjects().ok());
}

TEST(SkillTestFactory, MakeExecuteContextProvideWorldId) {
  auto skill_test_factory = SkillTestFactory();
  auto context = skill_test_factory.MakeExecuteContext({.world_id = "foobar"});
  EXPECT_EQ(context->object_world().GetWorldID(), "foobar");
}

TEST(SkillTestFactory, MakePreviewContextProvideAlmostEverything) {
  auto canceller =
      std::make_shared<SkillCancellationManager>(absl::ZeroDuration());
  auto equipment_pack = EquipmentPack();
  ASSERT_TRUE(equipment_pack.Add("foo", {}).ok());
  auto logging_context = SkillLoggingContext{
      .skill_id = "bar",
  };
  auto motion_planner_service =
      std::make_shared<MockMotionPlannerServiceStub>();
  auto object_world_service = std::make_shared<MockObjectWorldServiceStub>();

  auto skill_test_factory = SkillTestFactory();

  auto context = skill_test_factory.MakePreviewContext({
      .canceller = canceller.get(),
      .equipment_pack = equipment_pack,
      .logging_context = logging_context,
      .motion_planner_service = motion_planner_service,
      .object_world_service = object_world_service,
  });

  EXPECT_EQ(&context->canceller(), canceller.get());
  EXPECT_TRUE(equipment_pack.GetHandle("foo").ok());
  EXPECT_EQ(context->logging_context().skill_id, "bar");
  EXPECT_CALL(*motion_planner_service, ClearCache(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->motion_planner().ClearCache().ok());
  EXPECT_CALL(*object_world_service, ListObjects(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->object_world().ListObjects().ok());
}

TEST(SkillTestFactory, MakeGetFootprintContextProvideAlmostEverything) {
  auto canceller =
      std::make_shared<SkillCancellationManager>(absl::ZeroDuration());
  auto equipment_pack = EquipmentPack();
  ASSERT_TRUE(equipment_pack.Add("foo", {}).ok());
  auto logging_context = SkillLoggingContext{
      .skill_id = "bar",
  };
  auto motion_planner_service =
      std::make_shared<MockMotionPlannerServiceStub>();
  auto object_world_service = std::make_shared<MockObjectWorldServiceStub>();

  auto skill_test_factory = SkillTestFactory();

  auto context = skill_test_factory.MakeGetFootprintContext({
      .equipment_pack = equipment_pack,
      .motion_planner_service = motion_planner_service,
      .object_world_service = object_world_service,
  });

  EXPECT_TRUE(equipment_pack.GetHandle("foo").ok());
  EXPECT_CALL(*motion_planner_service, ClearCache(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->motion_planner().ClearCache().ok());
  EXPECT_CALL(*object_world_service, ListObjects(_, _, _))
      .WillOnce(Return(grpc::Status::OK));
  EXPECT_TRUE(context->object_world().ListObjects().ok());
}

TEST(SkillTestFactory, MakePreviewContextProvideWorldId) {
  auto skill_test_factory = SkillTestFactory();
  auto context = skill_test_factory.MakePreviewContext({.world_id = "foobar"});
  EXPECT_EQ(context->object_world().GetWorldID(), "foobar");
}

}  // namespace
}  // namespace skills
}  // namespace intrinsic
