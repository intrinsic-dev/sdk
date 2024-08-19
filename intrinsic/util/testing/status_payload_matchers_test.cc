// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/testing/status_payload_matchers.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/cord.h"
#include "google/protobuf/wrappers.pb.h"
#include "intrinsic/util/proto/type_url.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

using ::intrinsic::testing::EqualsProto;
using ::intrinsic::testing::WhenDeserializedAs;

namespace intrinsic::testing {
namespace {

TEST(StatusPayloadProtoMatcher, StatusMatches) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());

  EXPECT_THAT(s, StatusHasProtoPayload<google::protobuf::Int32Value>(
                     EqualsProto(int_value)));
}

TEST(StatusPayloadProtoMatcher, MissingPayloadDoesNotMatch) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());

  EXPECT_THAT(s, Not(StatusHasProtoPayload<google::protobuf::DoubleValue>(
                     EqualsProto(int_value))));
}

TEST(StatusPayloadProtoMatcher, OkStatusDoesNotMatch) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::OkStatus();
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());

  EXPECT_THAT(s, Not(StatusHasProtoPayload<google::protobuf::Int32Value>(
                     EqualsProto(int_value))));
}

TEST(StatusPayloadProtoMatcher, StatusOrMatches) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());
  absl::StatusOr<std::string> s_or = s;

  EXPECT_THAT(s_or, StatusHasProtoPayload<google::protobuf::Int32Value>(
                        EqualsProto(int_value)));
}

TEST(StatusPayloadProtoMatcher, MissingPayloadDoesNotMatchStatusOr) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());
  absl::StatusOr<std::string> s_or = s;

  EXPECT_THAT(s_or, Not(StatusHasProtoPayload<google::protobuf::DoubleValue>(
                        EqualsProto(int_value))));
}

TEST(StatusPayloadProtoMatcher, OkStatusOrDoesNotMatch) {
  absl::StatusOr<std::string> s = "Foo";

  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  EXPECT_THAT(s, Not(StatusHasProtoPayload<google::protobuf::Int32Value>(
                     EqualsProto(int_value))));
}

TEST(StatusPayloadGenericMatcher, StatusMatchesOnString) {
  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload("my_value", absl::Cord("Bar"));

  EXPECT_THAT(s, StatusHasGenericPayload("my_value", "Bar"));
}

TEST(StatusPayloadGenericMatcher, StatusMatchesOnProto) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());

  EXPECT_THAT(s, StatusHasGenericPayload(
                     AddTypeUrlPrefix<google::protobuf::Int32Value>(),
                     WhenDeserializedAs<google::protobuf::Int32Value>(
                         EqualsProto(int_value))));
}

TEST(StatusPayloadGenericMatcher, StatusMatchesHasPayload) {
  google::protobuf::Int32Value int_value;
  int_value.set_value(123);

  absl::Status s = absl::InvalidArgumentError("Foo");
  s.SetPayload(AddTypeUrlPrefix(int_value), int_value.SerializeAsCord());

  EXPECT_THAT(s, StatusHasGenericPayload(
                     AddTypeUrlPrefix<google::protobuf::Int32Value>()));
}

}  // namespace
}  // namespace intrinsic::testing
