// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_
#define INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_

#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "google/protobuf/message.h"
#include "grpcpp/impl/service_type.h"
#include "grpcpp/server.h"
#include "intrinsic/motion_planning/proto/motion_planner_service.grpc.pb.h"
#include "intrinsic/skills/cc/equipment_pack.h"
#include "intrinsic/skills/cc/skill_canceller.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/cc/skill_logging_context.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/world/proto/object_world_service.grpc.pb.h"

namespace intrinsic {
namespace skills {

// Calls a skill's Execute() method and optionally assigns its output to the
// specified result parameter.
template <typename TResult>
absl::Status ExecuteSkill(SkillExecuteInterface& skill,
                          const ExecuteRequest& request,
                          ExecuteContext& context, TResult* result) {
  INTR_ASSIGN_OR_RETURN(std::unique_ptr<::google::protobuf::Message> result_msg,
                        skill.Execute(request, context));

  if (result_msg->GetDescriptor()->full_name() !=
      TResult::descriptor()->full_name()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Skill returned result of type %s, but caller wants %s.",
        result_msg->GetDescriptor()->full_name(),
        TResult::descriptor()->full_name()));
  }
  if (result != nullptr &&
      !result->ParseFromString(result_msg->SerializeAsString())) {
    return absl::InternalError(
        "Could not parse result message as target type.");
  }

  return absl::OkStatus();
}
absl::Status ExecuteSkill(SkillExecuteInterface& skill,
                          const ExecuteRequest& request,
                          ExecuteContext& context);

// Calls a skill's Preview() method and optionally assigns its output to the
// specified result parameter.
template <typename TResult>
absl::Status PreviewSkill(SkillExecuteInterface& skill,
                          const PreviewRequest& request,
                          PreviewContext& context, TResult* result) {
  INTR_ASSIGN_OR_RETURN(std::unique_ptr<::google::protobuf::Message> result_msg,
                        skill.Preview(request, context));

  if (result_msg->GetDescriptor()->full_name() !=
      TResult::descriptor()->full_name()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Skill returned result of type %s, but caller wants %s.",
        result_msg->GetDescriptor()->full_name(),
        TResult::descriptor()->full_name()));
  }
  if (result != nullptr &&
      !result->ParseFromString(result_msg->SerializeAsString())) {
    return absl::InternalError(
        "Could not parse result message as target type.");
  }

  return absl::OkStatus();
}
absl::Status PreviewSkill(SkillExecuteInterface& skill,
                          const PreviewRequest& request,
                          PreviewContext& context);

// Creates objects needed to unit test skills.
//
// `intrinsic::skills::SkillInterface` defines methods for skills to implement.
// These methods accept request and context parameters.
// `SkillTestFactory` provides methods to make it easier to exercise these
// methods in unit tests.
//
// Example: Test Execute method on a skill that has no dependencies in its
//          manifest.
//
//    TEST(MySkillTest, Execute) {
//      auto skill_test_factory = SkillTestFactory();
//      auto skill = MySkill::CreateSkill();
//      MySkillParams params;
//
//      ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
//      std::unique_ptr<ExecuteContext> context =
//        skill_test_factory.MakeExecuteContext({});
//      ASSERT_THAT(skill->Execute(request, context), ::absl_testing::IsOk());
//    }
//
// Example: Test that an Execute method supports cancellation.
//
//    TEST(MySkillTest, ExecuteSupportsCancellation) {
//      auto skill_test_factory = SkillTestFactory();
//      auto skill = MySkill::CreateSkill();
//      MySkillParams params;
//
//      ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
//      SkillCancellationManager canceller(absl::Seconds(10));
//      std::unique_ptr<ExecuteContext> context =
//        skill_test_factory.MakeExecuteContext({.canceller = &canceller});
//
//      Thread cancel_skill([&canceller]() {
//        ASSERT_THAT(canceller.WaitForReady(), ::absl_testing::IsOk());
//        ASSERT_THAT(canceller.Cancel(), ::absl_testing::IsOk());
//      });
//
//      auto result = skill->Execute(request, *context);
//      cancel_skill.Join();
//
//      EXPECT_TRUE(absl::IsCancelled(result.status()));
//    }
//
// Example: Test Execute method on a skill that depends on one service, and you
//          have access to either a real or fake implementation of that service.
//
//    TEST(MySkillTest, Execute) {
//      auto skill_test_factory = SkillTestFactory();
//      auto skill = MySkill::CreateSkill();
//      MySkillParams params;
//      SomeServiceImpl some_service;
//      auto resource_handle = skill_test_factory.RunService(&some_service);
//      EquipmentPack equipment;
//      ASSERT_THAT(equipment.Add("some_slot", resource_handle),
//      ::absl_testing::IsOk());
//
//      ExecuteRequest request = skill_test_factory.MakeExecuteRequest(params);
//      std::unique_ptr<ExecuteContext> context =
//        skill_test_factory.MakeExecuteContext({.equipment_pack = equipment});
//      ASSERT_THAT(skill->Execute(request, context), ::absl_testing::IsOk());
//    }
//
// Example: Test Preview method on a skill that has no dependencies in its
//          manifest.
//
//    TEST(MySkillTest, Preview) {
//      auto skill_test_factory = SkillTestFactory();
//      auto skill = MySkill::CreateSkill();
//      MySkillParams params;
//
//      PreviewRequest request = skill_test_factory.MakePreviewRequest(params);
//      std::unique_ptr<PreviewContext> context =
//        skill_test_factory.MakePreviewContext({});
//      ASSERT_THAT(skill->Preview(request, context), ::absl_testing::IsOk());
//    }
//
class SkillTestFactory final {
 public:
  SkillTestFactory();
  ~SkillTestFactory() = default;

  // Runs a service that allows connections from localhost and returns a
  // ResourceHandle that can be used to connect to the service.
  // This call does not take ownership of the service, but it does create and
  // keep ownership of a gRPC server. The gRPC server is destroyed when the
  // SkillTestFactory is destroyed.
  intrinsic_proto::resources::ResourceHandle RunService(grpc::Service* service);

  // Creates an `ExecuteRequest` for testing a skill's Execute() method.
  //
  // See `ExecuteRequest` for the meanings of the arguments to this function.
  ExecuteRequest MakeExecuteRequest(
      const ::google::protobuf::Message& params,
      ::google::protobuf::Message* param_defaults = nullptr);

  // Creates a `PreviewRequest` for testing a skill's Preview() method.
  //
  // See `PreviewRequest` for the meanings of the arguments to this function.
  PreviewRequest MakePreviewRequest(
      const ::google::protobuf::Message& params,
      ::google::protobuf::Message* param_defaults = nullptr);

  // Initializes an `ExecuteContext` for testing a skill's Execute() method.
  //
  // All fields are optional.
  //
  // `canceller` holds a SkillCanceller instance that can be used to cancel a
  // call to a skill. You probably want to pass a `SkillCancellationManager`
  // instance. The struct does not retain ownership of the canceller.
  // If provided, the caller must ensure that the instance remains valid for the
  // lifetime of the `ExecuteContext` instance.
  //
  // `equipment_pack` holds a set of equipment containing resource handles that
  // can be used to connect to services needed by the skill. See `RunService`
  // for a convenient way to create service instances and resource handles.
  //
  // `logging_context` holds a SkillLoggingContext instance that can be used to
  // log information about the skill.
  //
  // `world_id` holds the id of the world that the skill should use.
  //
  // `motion_planner_service` holds a stub to a `MotionPlannerService` instance
  // that the skill can use. If not provided, `MakeExecuteContext` will create
  // a mock instance.
  //
  // `object_world_service` holds a stub to an `ObjectWorldService` that the
  // skill can use. If not provided, `MakeExecuteContext` will create a mock
  // instance.
  struct ExecuteContextInitializer {
    // If provided the canceller instance remains owned by the caller.
    SkillCanceller* canceller = nullptr;
    std::optional<EquipmentPack> equipment_pack;
    std::optional<SkillLoggingContext> logging_context;
    std::string world_id = "fake_world";
    std::shared_ptr<
        intrinsic_proto::motion_planning::MotionPlannerService::StubInterface>
        motion_planner_service;
    std::shared_ptr<intrinsic_proto::world::ObjectWorldService::StubInterface>
        object_world_service;
  };

  // Creates an `ExecuteContext` for testing a skill's Execute() method.
  //
  // See `ExecuteContextInitializer` to learn how to pass arguments to this
  // function.
  std::unique_ptr<ExecuteContext> MakeExecuteContext(
      const ExecuteContextInitializer& initializer);

  // Initializes an `PreviewContext` for testing a skill's Preview() method.
  //
  // All fields are optional. See `ExecuteContextInitializer` for the usage
  // of the fields as they are the same for `PreviewContextInitializer`.
  struct PreviewContextInitializer {
    // If provided the canceller instance remains owned by the caller.
    SkillCanceller* canceller = nullptr;
    std::optional<EquipmentPack> equipment_pack;
    std::optional<SkillLoggingContext> logging_context;
    std::string world_id = "fake_world";
    std::shared_ptr<
        intrinsic_proto::motion_planning::MotionPlannerService::StubInterface>
        motion_planner_service;
    std::shared_ptr<intrinsic_proto::world::ObjectWorldService::StubInterface>
        object_world_service;
  };

  // Creates a `PreviewContext` for testing a skill's Preview() method.
  //
  // See `PreviewContextInitializer` to learn how to pass arguments to this
  // function.
  std::unique_ptr<PreviewContext> MakePreviewContext(
      const PreviewContextInitializer& initializer);

 private:
  std::vector<std::unique_ptr<::grpc::Server>> servers_;
};

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_TESTING_SKILL_TEST_UTILS_H_
