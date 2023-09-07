// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/convert_c_realtime_status.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <algorithm>

#include "absl/status/status.h"
#include "intrinsic/icon/control/c_api/c_realtime_status.h"
#include "intrinsic/icon/utils/realtime_status.h"

namespace intrinsic::icon {
namespace {

using testing::SizeIs;
using testing::status::StatusIs;

TEST(ConvertXfaIconRealtimeStatus, FullSizeRealtimeStatusRoundtrip) {
  char max_size_buffer[kXfaIconRealtimeStatusMaxMessageLength];
  std::fill(&max_size_buffer[0],
            &max_size_buffer[kXfaIconRealtimeStatusMaxMessageLength], 'A');
  RealtimeStatus status = intrinsic::icon::InternalError(
      absl::string_view(max_size_buffer, sizeof(max_size_buffer)));
  RealtimeStatus round_tripped = ToRealtimeStatus(FromRealtimeStatus(status));
  EXPECT_EQ(round_tripped.code(), status.code());
  EXPECT_EQ(round_tripped.message(), status.message());
}

TEST(ConvertXfaIconRealtimeStatus, AbslStatusRoundtripGetsTruncated) {
  char longer_buffer[kXfaIconRealtimeStatusMaxMessageLength * 2];
  std::fill(&longer_buffer[0],
            &longer_buffer[kXfaIconRealtimeStatusMaxMessageLength * 2], 'A');
  absl::Status status = absl::InternalError(
      absl::string_view(longer_buffer, sizeof(longer_buffer)));
  EXPECT_THAT(
      ToAbslStatus(FromAbslStatus(status)),
      StatusIs(status.code(), SizeIs(kXfaIconRealtimeStatusMaxMessageLength)));
}

}  // namespace
}  // namespace intrinsic::icon
