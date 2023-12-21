// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/annotate.h"

#include <gtest/gtest.h>

#include <optional>

#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "google/protobuf/wrappers.pb.h"
#include "intrinsic/util/status/status_builder.h"

namespace intrinsic {
namespace {

TEST(AnnotateError, AddsMessage) {
  absl::Status original_status = absl::InvalidArgumentError("Foo");
  absl::Status annotated_status = AnnotateError(original_status, "Bar");

  EXPECT_EQ(original_status.message(), "Foo");
  EXPECT_EQ(annotated_status.message(), "Foo; Bar");
  EXPECT_EQ(annotated_status.code(), original_status.code());
}

TEST(AnnotateError, IgnoresOnOkStatus) {
  absl::Status original_status = absl::OkStatus();
  absl::Status annotated_status = AnnotateError(original_status, "Bar");

  EXPECT_EQ(original_status.message(), "");
  EXPECT_EQ(annotated_status.message(), "");
  EXPECT_EQ(annotated_status.code(), original_status.code());
}

TEST(AnnotateError, CopiesPayload) {
  google::protobuf::Int64Value payload_value;
  payload_value.set_value(123);
  absl::Status original_status = InvalidArgumentErrorBuilder().SetPayload(
                                     payload_value.GetDescriptor()->full_name(),
                                     payload_value.SerializeAsCord())
                                 << "Foo";
  absl::Status annotated_status = AnnotateError(original_status, "Bar");

  EXPECT_EQ(original_status.message(), "Foo");
  EXPECT_EQ(annotated_status.message(), "Foo; Bar");
  EXPECT_EQ(annotated_status.code(), original_status.code());
  std::optional<absl::Cord> result_payload = annotated_status.GetPayload(
      google::protobuf::Int64Value::descriptor()->full_name());
  ASSERT_TRUE(result_payload.has_value());
  google::protobuf::Int64Value result_value;
  result_value.ParseFromCord(*result_payload);
  EXPECT_EQ(result_value.value(), 123);
}

}  // namespace
}  // namespace intrinsic
