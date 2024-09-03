// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/skills/cc/skill_interface_utils.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <algorithm>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/duration.pb.h"
#include "google/protobuf/message.h"
#include "intrinsic/skills/cc/skill_interface.h"
#include "intrinsic/skills/internal/preview_context_impl.h"
#include "intrinsic/skills/proto/prediction.pb.h"
#include "intrinsic/skills/testing/echo_skill.pb.h"
#include "intrinsic/skills/testing/skill_test_utils.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace skills {
namespace {

using ::absl_testing::StatusIs;
using ::testing::HasSubstr;

// A skill whose Execute() echos the input, and whose Preview() calls Execute().
class PreviewViaExecuteSkill : public SkillExecuteInterface {
 public:
  PreviewViaExecuteSkill() = default;

  absl::StatusOr<std::unique_ptr<google::protobuf::Message>> Execute(
      const ExecuteRequest& request, ExecuteContext& context) override {
    INTR_ASSIGN_OR_RETURN(
        auto params,
        request.params<intrinsic_proto::skills::EchoSkillParams>());

    auto result = std::make_unique<intrinsic_proto::skills::EchoSkillReturn>();
    result->set_foo(params.foo());

    return result;
  }

  absl::StatusOr<std::unique_ptr<::google::protobuf::Message>> Preview(
      const PreviewRequest& request, PreviewContext& context) override {
    return PreviewViaExecute(*this, request, context);
  }
};

TEST(PreviewViaExecuteTest, PreviewViaExecuteCallsExecute) {
  auto skill_test_factory = SkillTestFactory();
  PreviewViaExecuteSkill skill;

  intrinsic_proto::skills::EchoSkillParams params;
  params.set_foo("foo");
  auto request = skill_test_factory.MakePreviewRequest(params);
  auto context = skill_test_factory.MakePreviewContext({});

  intrinsic_proto::skills::EchoSkillReturn result;
  ASSERT_OK(PreviewSkill(skill, request, *context, &result));

  EXPECT_EQ(result.foo(), "foo");
}

intrinsic_proto::skills::TimedWorldUpdate MakeUpdate(
    std::optional<int> start_time_seconds, int time_until_update_seconds,
    absl::string_view frame_name) {
  intrinsic_proto::skills::TimedWorldUpdate update;
  if (start_time_seconds.has_value()) {
    update.mutable_start_time()->set_seconds(*start_time_seconds);
  }
  update.mutable_time_until_update()->set_seconds(time_until_update_seconds);
  update.mutable_world_updates()
      ->add_updates()
      ->mutable_create_frame()
      ->set_new_frame_name(frame_name);

  return update;
}

}  // namespace
}  // namespace skills
}  // namespace intrinsic
