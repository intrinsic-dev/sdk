// Copyright 2023 Intrinsic Innovation LLC

#include <gtest/gtest.h>

#include "intrinsic/util/thread/stop_token.h"

namespace intrinsic {
namespace {

TEST(StopSourceTest, StopSourceWithNoState) {
  StopSource stop_source(detail::NoState);
  EXPECT_FALSE(stop_source.stop_possible());
  EXPECT_FALSE(stop_source.stop_requested());
}

TEST(StopSourceTest, StopSourceWithState) {
  StopSource stop_source;
  EXPECT_TRUE(stop_source.stop_possible());
  EXPECT_FALSE(stop_source.stop_requested());
}

TEST(StopSourceTest, StopSourceCanBeStopped) {
  StopSource stop_source;
  EXPECT_TRUE(stop_source.request_stop());
  EXPECT_TRUE(stop_source.stop_requested());
}

TEST(StopSourceTest, StopSourceWithoutStateCannotBeStopped) {
  StopSource stop_source(detail::NoState);
  EXPECT_FALSE(stop_source.stop_possible());
  EXPECT_FALSE(stop_source.request_stop());
}

}  // namespace
}  // namespace intrinsic
