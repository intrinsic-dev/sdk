// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

#include <gtest/gtest.h>

namespace intrinsic {

TEST(ZenohHandleTest, AddTopicPrefix) {
  EXPECT_EQ(*ZenohHandle::add_topic_prefix("foo"), "in/foo");
  EXPECT_EQ(*ZenohHandle::add_topic_prefix("/foo"), "in/foo");
  EXPECT_EQ(ZenohHandle::add_topic_prefix("").ok(), false);
}

TEST(ZenohHandleTest, RemoveTopicPrefix) {
  EXPECT_EQ(*ZenohHandle::remove_topic_prefix("in/foo"), "/foo");
  EXPECT_EQ(*ZenohHandle::remove_topic_prefix("in/"), "/");
  EXPECT_EQ(ZenohHandle::remove_topic_prefix("").ok(), false);
}

}  // namespace intrinsic
