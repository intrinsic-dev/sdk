// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_util/zenoh_config.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <string>

#include "absl/flags/flag.h"
#include "intrinsic/util/testing/gtest_wrapper.h"

using ::testing::HasSubstr;

namespace intrinsic {

TEST(ZenohConfigTest, TestRouterFlag) {
  const std::string test_router_endpoint("tcp/foo.bar.baz:12345");
  absl::SetFlag(&FLAGS_zenoh_router, test_router_endpoint);
  std::string config(GetZenohPeerConfig());
  EXPECT_THAT(config, HasSubstr(test_router_endpoint));
}

}  // namespace intrinsic
