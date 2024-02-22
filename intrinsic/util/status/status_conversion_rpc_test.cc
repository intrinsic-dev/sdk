// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_conversion_rpc.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "absl/status/status.h"
#include "google/protobuf/wrappers.pb.h"
#include "google/rpc/code.pb.h"
#include "google/rpc/status.pb.h"
#include "intrinsic/util/proto/type_url.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

namespace intrinsic {
namespace {

using ::testing::AllOf;
using ::testing::Eq;
using ::testing::Optional;
using ::testing::ResultOf;
using ::testing::SizeIs;

TEST(MakeStatusFromRpcStatus, CodeAndMessageStored) {
  google::rpc::Status rpc_status;
  rpc_status.set_code(google::rpc::Code::DEADLINE_EXCEEDED);
  rpc_status.set_message("Oh no!");

  absl::Status absl_status = MakeStatusFromRpcStatus(rpc_status);
  EXPECT_EQ(absl_status.code(), absl::StatusCode::kDeadlineExceeded);
  EXPECT_EQ(absl_status.message(), "Oh no!");
}

TEST(SaveStatusAsRpcStatus, CodeAndMessageStored) {
  auto absl_status = absl::DeadlineExceededError("Oh no!");

  google::rpc::Status rpc_status = SaveStatusAsRpcStatus(absl_status);
  EXPECT_EQ(rpc_status.message(), "Oh no!");
  EXPECT_EQ(rpc_status.code(), google::rpc::Code::DEADLINE_EXCEEDED);
}

TEST(SaveStatusAsRpcStatus, TypeUrlPrefix) {
  auto absl_status = absl::DeadlineExceededError("Oh no!");

  google::protobuf::Int64Value custom_payload;
  custom_payload.set_value(123);
  absl_status.SetPayload(
      AddTypeUrlPrefix(google::protobuf::Int64Value::descriptor()->full_name()),
      custom_payload.SerializeAsCord());

  google::rpc::Status rpc_status = SaveStatusAsRpcStatus(absl_status);
  EXPECT_THAT(rpc_status.details(), SizeIs(1));
}

TEST(MakeStatusFromRpcStatus, TypeUrlPrefixRemoved) {
  google::protobuf::Int64Value custom_payload;
  custom_payload.set_value(123);

  google::rpc::Status rpc_status;
  rpc_status.set_code(google::rpc::Code::DEADLINE_EXCEEDED);
  rpc_status.set_message("Oh no!");
  rpc_status.add_details()->PackFrom(custom_payload);

  absl::Status absl_status = MakeStatusFromRpcStatus(rpc_status);
  EXPECT_THAT(
      absl_status,
      AllOf(ResultOf([](const absl::Status& status) { return status.code(); },
                     Eq(absl::StatusCode::kDeadlineExceeded)),
            ResultOf(
                [](const absl::Status& status) {
                  return status.GetPayload(AddTypeUrlPrefix(
                      google::protobuf::Int64Value::descriptor()->full_name()));
                },
                Optional(custom_payload.SerializeAsCord()))));
}

}  // namespace
}  // namespace intrinsic
