// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/get_extended_status.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <optional>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "google/rpc/code.pb.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/support/status.h"
#include "intrinsic/util/proto/parse_text_proto.h"
#include "intrinsic/util/status/extended_status.pb.h"
#include "intrinsic/util/status/status_builder.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/status/status_conversion_rpc.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace {

using ::intrinsic::ParseTextOrDie;
using ::intrinsic::testing::EqualsProto;
using ::testing::Optional;

TEST(GetExtendedStatus, FromAbslStatus) {
  absl::Status s = static_cast<absl::Status>(
      StatusBuilder(absl::StatusCode::kInternal)
          .SetExtendedStatusCode("ai.intrinsic.test", 123)
          .SetExtendedStatusTitle("Foo"));
  EXPECT_THAT(GetExtendedStatus(s), Optional(EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 123 }
                title: "Foo"
              )pb")));
}

TEST(GetExtendedStatus, FromAbslStatusWithoutExtendedStatus) {
  absl::Status s = absl::InternalError("Error");
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromAbslOkStatus) {
  absl::Status s = absl::OkStatus();
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromAbslStatusOr) {
  absl::StatusOr<std::string> s = static_cast<absl::Status>(
      StatusBuilder(absl::StatusCode::kInternal)
          .SetExtendedStatusCode("ai.intrinsic.test", 123)
          .SetExtendedStatusTitle("Foo"));
  EXPECT_THAT(GetExtendedStatus(s), Optional(EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 123 }
                title: "Foo"
              )pb")));
}

TEST(GetExtendedStatus, FromAbslStatusOrWithoutExtendedStatus) {
  absl::StatusOr<std::string> s = absl::InternalError("Error");
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromAbslOkStatusOrWithoutExtendedStatus) {
  absl::StatusOr<std::string> s = "bar";
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromGrpcStatus) {
  grpc::Status s = ToGrpcStatus(static_cast<absl::Status>(
      StatusBuilder(absl::StatusCode::kInternal)
          .SetExtendedStatusCode("ai.intrinsic.test", 123)
          .SetExtendedStatusTitle("Foo")));
  EXPECT_THAT(GetExtendedStatus(s), Optional(EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 123 }
                title: "Foo"
              )pb")));
}

TEST(GetExtendedStatus, FromGrpcStatusWithoutExtendedStatus) {
  grpc::Status s = grpc::Status(grpc::StatusCode::INTERNAL, "Foo");
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromGrpcOkStatus) {
  grpc::Status s = grpc::Status::OK;
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromGoogleRpcStatus) {
  google::rpc::Status s = ToGoogleRpcStatus(static_cast<absl::Status>(
      StatusBuilder(absl::StatusCode::kInternal)
          .SetExtendedStatusCode("ai.intrinsic.test", 123)
          .SetExtendedStatusTitle("Foo")));
  EXPECT_THAT(GetExtendedStatus(s), Optional(EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 123 }
                title: "Foo"
              )pb")));
}

TEST(GetExtendedStatus, FromGoogleRpcStatusWithMultiplePayloadsTakesLast) {
  google::rpc::Status s;
  s.set_code(google::rpc::INTERNAL);
  s.add_details()->PackFrom(
      ParseTextOrDie<intrinsic_proto::status::ExtendedStatus>(R"pb(
        status_code { component: "ai.intrinsic.test" code: 123 }
        title: "Foo"
      )pb"));
  s.add_details()->PackFrom(
      ParseTextOrDie<intrinsic_proto::status::ExtendedStatus>(R"pb(
        status_code { component: "ai.intrinsic.test" code: 234 }
        title: "Bar"
      )pb"));
  EXPECT_THAT(GetExtendedStatus(s), Optional(EqualsProto(R"pb(
                status_code { component: "ai.intrinsic.test" code: 234 }
                title: "Bar"
              )pb")));
}

TEST(GetExtendedStatus, FromGoogleRpcStatusWithoutExtendedStatus) {
  google::rpc::Status s;
  s.set_code(google::rpc::INTERNAL);
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

TEST(GetExtendedStatus, FromGoogleRpcOkStatus) {
  google::rpc::Status s;
  s.set_code(google::rpc::OK);
  EXPECT_EQ(GetExtendedStatus(s), std::nullopt);
}

}  // namespace
}  // namespace intrinsic
