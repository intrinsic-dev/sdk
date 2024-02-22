// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_conversion_grpc.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <optional>

#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "google/protobuf/wrappers.pb.h"
#include "grpcpp/support/status.h"
#include "intrinsic/util/proto/type_url.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace {

TEST(StatusConversionGrpcTest, AbslStatusToGrpcStatusRoundTrip) {
  absl::Status absl_status = absl::InternalError("A terrible thing happened!");
  google::protobuf::StringValue value;
  value.set_value("Foo");
  absl_status.SetPayload(AddTypeUrlPrefix(value.GetDescriptor()->full_name()),
                         value.SerializeAsCord());

  // Round trip through grpc status.
  grpc::Status grpc_status = ToGrpcStatus(absl_status);
  absl::Status returned_status = ToAbslStatus(grpc_status);

  EXPECT_EQ(returned_status.code(), absl_status.code());
  EXPECT_EQ(returned_status.message(), absl_status.message());

  google::protobuf::StringValue read_value;

  std::optional<absl::Cord> read_payload = returned_status.GetPayload(
      AddTypeUrlPrefix(value.GetDescriptor()->full_name()));
  ASSERT_TRUE(read_payload.has_value());
  ASSERT_TRUE(read_value.ParseFromCord(*read_payload));
  EXPECT_THAT(read_value.value(), ::testing::Eq(value.value()));
}

}  // namespace
}  // namespace intrinsic
