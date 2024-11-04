// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_specs.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <functional>
#include <string>
#include <utility>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/time/civil_time.h"
#include "absl/time/time.h"
#include "intrinsic/assets/proto/status_spec.pb.h"
#include "intrinsic/util/proto/parse_text_proto.h"
#include "intrinsic/util/status/extended_status.pb.h"
#include "intrinsic/util/status/status_builder.h"
#include "intrinsic/util/status/status_macros.h"
#include "intrinsic/util/testing/gtest_wrapper.h"
#include "intrinsic/util/testing/status_payload_matchers.h"

namespace intrinsic {
namespace {

using ::absl_testing::StatusIs;
using ::intrinsic::ParseTextProtoOrDie;
using ::intrinsic::testing::EqualsProto;
using ::intrinsic::testing::StatusHasProtoPayload;
using ::testing::HasSubstr;
using ::testing::ValuesIn;

struct StatusSpecTestCase {
  std::string name;
  std::function<void()> init;
};

class StatusSpecsTest : public ::testing::TestWithParam<StatusSpecTestCase> {
 public:
  void SetUp() override { GetParam().init(); }
  void TearDown() override { ClearExtendedStatusSpecs(); }
};

INSTANTIATE_TEST_SUITE_P(
    StatusSpecTestSuite, StatusSpecsTest,
    ValuesIn<StatusSpecTestCase>(
        {//
         {.name = "FromVector",
          .init =
              []() {
                CHECK_OK(InitExtendedStatusSpecs(
                    "ai.intrinsic.test",
                    {ParseTextProtoOrDie(
                         R"pb(
                           code: 10001
                           title: "Error 1"
                           recovery_instructions: "Test instructions 1"
                         )pb"),
                     ParseTextProtoOrDie(R"pb(
                       code: 10002
                       title: "Error 2"
                       recovery_instructions: "Test instructions 2"
                     )pb")}));
              }},
         {.name = "FromRepeatedPtrField",
          .init =
              []() {
                intrinsic_proto::assets::StatusSpecs specs =
                    ParseTextProtoOrDie(R"pb(
                      status_info:
                      [ {
                        code: 10001
                        title: "Error 1"
                        recovery_instructions: "Test instructions 1"
                      }
                        , {
                          code: 10002
                          title: "Error 2"
                          recovery_instructions: "Test instructions 2"
                        }]
                    )pb");
                CHECK_OK(InitExtendedStatusSpecs("ai.intrinsic.test",
                                                 specs.status_info()));
              }}}),
    [](const ::testing::TestParamInfo<StatusSpecTestCase>& info) {
      return info.param.name;
    });

TEST_P(StatusSpecsTest, LoadedSpecs) {
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());

  EXPECT_THAT(CreateExtendedStatus(10001, "error 1", {.timestamp = t}),
              EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 10001 }
                timestamp { seconds: 1711453873 }
                title: "Error 1"
                external_report {
                  message: "error 1"
                  instructions: "Test instructions 1"
                }
              )pb"));

  EXPECT_THAT(CreateExtendedStatus(10002, "error 2", {.timestamp = t}),
              EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 10002 }
                timestamp { seconds: 1711453873 }
                title: "Error 2"
                external_report {
                  message: "error 2"
                  instructions: "Test instructions 2"
                }
              )pb"));

  EXPECT_THAT(
      CreateExtendedStatus(666, "does not exist", {.timestamp = t}),
      EqualsProto(R"pb(
        status_code { component: "ai.intrinsic.test" code: 666 }
        timestamp { seconds: 1711453873 }
        external_report { message: "does not exist" }
        context {
          status_code { component: "ai.intrinsic.errors" code: 604 }
          title: "Error code not declared"
          severity: WARNING
          external_report {
            message: "The code ai.intrinsic.test:666 has not been declared by the component."
            instructions: "Inform the owner of ai.intrinsic.test to add error 666 to the status specs file."
          }
        }
      )pb"));
}

TEST_P(StatusSpecsTest, AllOptionsAreSet) {
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());

  intrinsic_proto::data_logger::Context log_context;
  log_context.set_executive_plan_id(3354);

  intrinsic_proto::status::ExtendedStatus context_status_1;
  context_status_1.mutable_status_code()->set_component("Context");
  context_status_1.mutable_status_code()->set_code(123);
  intrinsic_proto::status::ExtendedStatus context_status_2;
  context_status_2.mutable_status_code()->set_component("Context");
  context_status_2.mutable_status_code()->set_code(234);

  EXPECT_THAT(
      CreateExtendedStatus(10001, "error 1",
                           {.timestamp = t,
                            .internal_report_message = "Int message",
                            .internal_report_instructions = "Int instructions",
                            .log_context = log_context,
                            .context = {context_status_1, context_status_2}}),
      EqualsProto(R"pb(
        status_code { component: "ai.intrinsic.test" code: 10001 }
        timestamp { seconds: 1711453873 }
        title: "Error 1"
        external_report {
          message: "error 1"
          instructions: "Test instructions 1"
        }
        internal_report {
          message: "Int message"
          instructions: "Int instructions"
        }
        related_to { log_context { executive_plan_id: 3354 } }
        context { status_code { component: "Context" code: 123 } }
        context { status_code { component: "Context" code: 234 } }
      )pb"));
}

TEST_P(StatusSpecsTest, CreateStatus) {
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  EXPECT_THAT(
      CreateStatus(10001, "error 1", absl::StatusCode::kInvalidArgument,
                   {.timestamp = t, .internal_report_message = "Internal"}),
      AllOf(StatusIs(absl::StatusCode::kInvalidArgument),
            StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                EqualsProto(R"pb(
                  status_code { component: "ai.intrinsic.test" code: 10001 }
                  timestamp { seconds: 1711453873 }
                  title: "Error 1"
                  external_report {
                    message: "error 1"
                    instructions: "Test instructions 1"
                  }
                  internal_report { message: "Internal" }
                )pb"))));
}

TEST_P(StatusSpecsTest, AttachExtendedStatus) {
  absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                 absl::UTCTimeZone());
  EXPECT_THAT(
      static_cast<absl::Status>(
          StatusBuilder(absl::StatusCode::kInternal)
              .With(AttachExtendedStatus(
                  10001, "error 1",
                  {.timestamp = t, .internal_report_message = "Internal"}))),
      StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
          EqualsProto(R"pb(
            status_code { component: "ai.intrinsic.test" code: 10001 }
            timestamp { seconds: 1711453873 }
            title: "Error 1"
            external_report {
              message: "error 1"
              instructions: "Test instructions 1"
            }
            internal_report { message: "Internal" }
          )pb")));
}

TEST(StatusSpecsInvalidTest, DuplicateFails) {
  EXPECT_THAT(InitExtendedStatusSpecs(
                  "ai.intrinsic.test",
                  {ParseTextProtoOrDie(
                       R"pb(
                         code: 10001
                         title: "Error 1"
                         recovery_instructions: "Test instructions 1"
                       )pb"),
                   ParseTextProtoOrDie(R"pb(
                     code: 10001
                     title: "Error 2"
                     recovery_instructions: "Test instructions 2"
                   )pb")}),
              StatusIs(absl::StatusCode::kInvalidArgument,
                       HasSubstr("declares error code 10001 twice")));
}

TEST_P(StatusSpecsTest, AttachExtendedStatusInReturnMacro) {
  auto erroring_func = [] { return absl::InvalidArgumentError("Foo"); };
  auto macro_func = [erroring_func]() -> absl::StatusOr<std::string> {
    absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                   absl::UTCTimeZone());
    INTR_RETURN_IF_ERROR(erroring_func())
        .With(AttachExtendedStatus(
            10001, "error 1",
            {.timestamp = t, .internal_report_message = "Internal"}));
    return "";
  };

  EXPECT_THAT(macro_func(),
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "ai.intrinsic.test" code: 10001 }
                    timestamp { seconds: 1711453873 }
                    title: "Error 1"
                    external_report {
                      message: "error 1"
                      instructions: "Test instructions 1"
                    }
                    internal_report { message: "Internal" }
                  )pb")));
}

TEST_P(StatusSpecsTest, AttachExtendedStatusInAssignMacro) {
  auto erroring_func = []() -> absl::StatusOr<std::string> {
    return absl::InvalidArgumentError("Foo");
  };
  auto macro_func = [erroring_func]() -> absl::StatusOr<std::string> {
    absl::Time t = absl::FromCivil(absl::CivilSecond(2024, 3, 26, 11, 51, 13),
                                   absl::UTCTimeZone());
    INTR_ASSIGN_OR_RETURN(
        std::string s, erroring_func(),
        std::move(_).With(AttachExtendedStatus(
            10001, "error 1",
            {.timestamp = t, .internal_report_message = "Internal"})));
    return "";
  };

  EXPECT_THAT(macro_func(),
              StatusHasProtoPayload<intrinsic_proto::status::ExtendedStatus>(
                  EqualsProto(R"pb(
                    status_code { component: "ai.intrinsic.test" code: 10001 }
                    timestamp { seconds: 1711453873 }
                    title: "Error 1"
                    external_report {
                      message: "error 1"
                      instructions: "Test instructions 1"
                    }
                    internal_report { message: "Internal" }
                  )pb")));
}

}  // namespace
}  // namespace intrinsic
