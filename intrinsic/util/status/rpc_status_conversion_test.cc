// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/rpc_status_conversion.h"

#include <gtest/gtest.h>

#include "absl/status/status.h"
#include "google/rpc/code.pb.h"
#include "google/rpc/status.pb.h"

namespace intrinsic {
namespace {

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

}  // namespace
}  // namespace intrinsic
