// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/thread/stop_token.h"

#include <gtest/gtest.h>

namespace intrinsic {
namespace {

TEST(StopTokenTest, StopSourceWithNoState) {
  StopToken stop_token;
  EXPECT_FALSE(stop_token.stop_possible());
  EXPECT_FALSE(stop_token.stop_requested());
}

TEST(StopTokenTest, StopSourceWithStateCanStop) {
  StopSource stop_source;
  StopToken stop_token = stop_source.get_token();
  EXPECT_TRUE(stop_token.stop_possible());
  EXPECT_FALSE(stop_token.stop_requested());
}

TEST(StopTokenTest, StopSourceWithStateStops) {
  StopSource stop_source;
  EXPECT_TRUE(stop_source.request_stop());
  StopToken stop_token = stop_source.get_token();
  EXPECT_TRUE(stop_token.stop_possible());
  EXPECT_TRUE(stop_token.stop_requested());
}

TEST(StopTokenTest, StopSourceWithStateStopsAfterTokenCreation) {
  StopSource stop_source;
  StopToken stop_token = stop_source.get_token();
  EXPECT_TRUE(stop_token.stop_possible());
  EXPECT_FALSE(stop_token.stop_requested());
  EXPECT_TRUE(stop_source.request_stop());
  EXPECT_TRUE(stop_token.stop_requested());
}

}  // namespace
}  // namespace intrinsic
