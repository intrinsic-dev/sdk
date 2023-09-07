// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/release/file_helpers.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include "file/base/path.h"
#include "google/rpc/status.pb.h"

namespace intrinsic {
namespace {

TEST(FileHelpers, RoundTrip) {
  google::rpc::Status sub_status;
  sub_status.set_code(3);
  sub_status.set_message("sub status message");

  google::rpc::Status my_status;
  my_status.set_code(10);
  my_status.set_message("a test string");
  my_status.add_details()->PackFrom(sub_status);

  auto filename = file::JoinPath(::testing::TempDir(), "round_trip.pbbin");
  ASSERT_OK(SetBinaryProto(filename, my_status));
  auto read_back_status_or = GetBinaryProto<google::rpc::Status>(filename);
  ASSERT_OK(read_back_status_or.status());

  EXPECT_THAT(*read_back_status_or, ::testing::EqualsProto(my_status));
}

TEST(FileHelpers, GetFileDoesNotExist) {
  auto filename =
      file::JoinPath(::testing::TempDir(), "non_existent_file.pbbin");
  auto read_back_status_or = GetBinaryProto<google::rpc::Status>(filename);
  EXPECT_THAT(read_back_status_or.status(),
              ::testing::status::StatusIs(absl::StatusCode::kInvalidArgument));
}

}  // namespace
}  // namespace intrinsic
