// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/pubsub_test_suite.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <memory>

#include "absl/synchronization/notification.h"
#include "intrinsic/platform/common/proto/test.pb.h"
#include "intrinsic/platform/pubsub/publisher_stats.h"
#include "intrinsic/platform/pubsub/pubsub.h"
#include "util/task/codes.pb.h"

namespace intrinsic {

// Test instantiation of a class that implements PubSub.
TEST_P(PubSubTestSuite, TestInstance) {}

// Test Publishing.
TEST_P(PubSubTestSuite, TestPublishIncrementsCounter) {
  proto::TestMessageStock message;
  absl::string_view topic = "stocks";
  PubSub pubsub;
  EXPECT_EQ(0, intrinsic::internal::MessagesPublished(topic));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher(topic, TopicConfig{}));
  ASSERT_OK(pub.Publish(message));
  EXPECT_EQ(1, intrinsic::internal::MessagesPublished(topic));
  ASSERT_OK(pub.Publish(message));
  EXPECT_EQ(2, intrinsic::internal::MessagesPublished(topic));
  for (int i = 0; i < 10; i++) {
    EXPECT_EQ(2 + i, intrinsic::internal::MessagesPublished(topic));
    ASSERT_OK(pub.Publish(message));
  }
}

// Test subscription that receives a publication.
TEST_P(PubSubTestSuite, TestSubscriptionPublicationSameProtoMessage) {
  absl::Notification stock_notification;

  absl::string_view topic = "stocks";
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageStock>(
          topic, TopicConfig{},
          [&stock_notification](const proto::TestMessageStock& message) {
            EXPECT_EQ(message.symbol(), "GOOG");
            EXPECT_EQ(message.value(), 1080.91);
            stock_notification.Notify();
          },
          [](absl::string_view packet, const absl::Status& error) {}));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher(topic, TopicConfig{}));
  EXPECT_FALSE(stock_notification.HasBeenNotified());

  proto::TestMessageStock message;
  message.set_symbol("GOOG");
  message.set_value(1080.91);
  EXPECT_OK(pub.Publish(message));

  stock_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(stock_notification.HasBeenNotified());
}

// Test subscription that receives a publication with a different type.
TEST_P(PubSubTestSuite, TestSubscriptionPublicationDifferentType) {
  absl::Notification stock_notification;

  absl::string_view topic = "stocks";
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageString>(
          topic, TopicConfig{}, [](const proto::TestMessageString& message) {},
          [&stock_notification](absl::string_view packet,
                                const absl::Status& error) {
            EXPECT_THAT(error, testing::status::StatusIs(
                                   util::error::INVALID_ARGUMENT));
            stock_notification.Notify();
          }));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher(topic, TopicConfig{}));
  EXPECT_FALSE(stock_notification.HasBeenNotified());

  proto::TestMessageStock message;
  message.set_symbol("GOOG");
  message.set_value(1080.91);
  auto status = pub.Publish(message);
  if (!status.ok()) {
    // DDS pubsub will refuse to publish the mistyped message.
    stock_notification.Notify();
  }

  stock_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(stock_notification.HasBeenNotified());
}

// Test subscription that does not receive same message published on a different
// topic.
TEST_P(PubSubTestSuite, TestSubscriptionPublicationSameMessageDifferentTopic) {
  absl::Notification stock_notification;
  PubSub pubsub;

  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageStock>(
          "stocks", TopicConfig{},
          [&stock_notification](const proto::TestMessageStock& message) {
            EXPECT_EQ(message.symbol(), "GOOG");
            EXPECT_EQ(message.value(), 1080.91);
            stock_notification.Notify();
          },
          [](absl::string_view packet, const absl::Status& error) {}));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher("news", TopicConfig{}));
  EXPECT_FALSE(stock_notification.HasBeenNotified());

  proto::TestMessageStock message;
  message.set_symbol("GOOG");
  message.set_value(1080.91);
  EXPECT_OK(pub.Publish(message));

  stock_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_FALSE(stock_notification.HasBeenNotified());
}

// Test a single subscription that updates its callback between the first and
// the second publication to the same topic.
TEST_P(PubSubTestSuite, TestDoubleSubscription) {
  absl::Notification sunny_notification;
  absl::Notification rainy_notification;
  absl::string_view topic = "weather";
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(
      auto sub1,
      pubsub.CreateSubscription<proto::TestMessageString>(
          topic, TopicConfig{},
          [&sunny_notification](const proto::TestMessageString& message) {
            if (!sunny_notification.HasBeenNotified()) {
              EXPECT_EQ(message.data(), "Sunny");
              sunny_notification.Notify();
            }
          }));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher(topic, TopicConfig{}));
  EXPECT_FALSE(sunny_notification.HasBeenNotified());

  proto::TestMessageString message;
  message.set_data("Sunny");
  EXPECT_OK(pub.Publish(message));

  sunny_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(sunny_notification.HasBeenNotified());

  ASSERT_OK_AND_ASSIGN(
      auto sub2,
      pubsub.CreateSubscription<proto::TestMessageString>(
          topic, TopicConfig{},
          [&rainy_notification](const proto::TestMessageString& message) {
            if (message.data() == "Rainy") {
              rainy_notification.Notify();
            }
          }));

  EXPECT_FALSE(rainy_notification.HasBeenNotified());

  message.set_data("Rainy");
  EXPECT_OK(pub.Publish(message));

  rainy_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(rainy_notification.HasBeenNotified());
}

// Test subscription that receives four publications.
TEST_P(PubSubTestSuite, TestSubscriptionWithFourPublications) {
  absl::Notification stock_notification;
  absl::string_view topic = "stocks";
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageStock>(
          topic, TopicConfig{},
          [&stock_notification](const proto::TestMessageStock& message) {
            static int receive_sequence = 0;

            EXPECT_EQ(message.symbol(), "GOOG");
            EXPECT_EQ(message.value(), 1080.91);

            if (++receive_sequence == 4) {
              stock_notification.Notify();
            }
          },
          subscription_error_callback_fail_when_invoked_));
  ASSERT_OK_AND_ASSIGN(auto pub, pubsub.CreatePublisher(topic, TopicConfig{}));
  EXPECT_FALSE(stock_notification.HasBeenNotified());

  proto::TestMessageStock message;
  message.set_symbol("GOOG");
  message.set_value(1080.91);

  EXPECT_OK(pub.Publish(message));
  EXPECT_OK(pub.Publish(message));
  EXPECT_OK(pub.Publish(message));
  EXPECT_OK(pub.Publish(message));

  stock_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(stock_notification.HasBeenNotified());
}

// Test subscription that receives message published from different PubSub
// instance.
// Temporarily disabled because of participant discovery issues when running
// on forge. This test currently only passes locally.
TEST_P(PubSubTestSuite, TestSubscriptionPublicationDifferentPubSubInstances) {
  absl::Notification stock_notification;
  absl::string_view topic = "stocks";
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageStock>(
          topic, TopicConfig{},
          [&stock_notification](const proto::TestMessageStock& message) {
            EXPECT_EQ(message.symbol(), "GOOG");
            EXPECT_EQ(message.value(), 1080.91);
            stock_notification.Notify();
          },
          subscription_error_callback_fail_when_invoked_));
  EXPECT_FALSE(stock_notification.HasBeenNotified());

  proto::TestMessageStock message;
  message.set_symbol("GOOG");
  message.set_value(1080.91);

  PubSub second_pubsub;
  ASSERT_OK_AND_ASSIGN(auto pub,
                       second_pubsub.CreatePublisher(topic, TopicConfig{}));
  EXPECT_OK(pub.Publish(message));

  stock_notification.WaitForNotificationWithTimeout(absl::Seconds(5));
  EXPECT_TRUE(stock_notification.HasBeenNotified());
}

// Test assignment to an existing subscription (its move-assign operator)
TEST_P(PubSubTestSuite, TestReassignedSubscription) {
  absl::string_view first_topic = "first_topic";
  absl::string_view second_topic = "second_topic";
  absl::Notification first_notification;
  absl::Notification second_notification;
  PubSub pubsub;
  ASSERT_OK_AND_ASSIGN(auto first_pub,
                       pubsub.CreatePublisher(first_topic, TopicConfig{}));
  ASSERT_OK_AND_ASSIGN(auto second_pub,
                       pubsub.CreatePublisher(second_topic, TopicConfig{}));
  ASSERT_OK_AND_ASSIGN(
      auto sub,
      pubsub.CreateSubscription<proto::TestMessageString>(
          first_topic, TopicConfig{},
          [&first_notification](const proto::TestMessageString& message) {
            EXPECT_FALSE(first_notification.HasBeenNotified());
            EXPECT_EQ(message.data(), "first_message");
            first_notification.Notify();
          }));
  EXPECT_FALSE(first_notification.HasBeenNotified());

  proto::TestMessageString first_message;
  first_message.set_data("first_message");
  EXPECT_OK(first_pub.Publish(first_message));

  first_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(first_notification.HasBeenNotified());

  // Assign a new subscription that overwrites the previous subscription.
  ASSERT_OK_AND_ASSIGN(
      sub, pubsub.CreateSubscription<proto::TestMessageString>(
               second_topic, TopicConfig{},
               [&second_notification](const proto::TestMessageString& message) {
                 EXPECT_FALSE(second_notification.HasBeenNotified());
                 EXPECT_EQ(message.data(), "second_message");
                 second_notification.Notify();
               }));

  EXPECT_FALSE(second_notification.HasBeenNotified());

  // This Publish() call to the previously-subscribed topic should now be
  // a no-op, since this topic no longer has any subscribers. It's in this
  // test to ensure that this Publish() call doesn't cause a crash due to
  // a lurking subscription with an invalid callback pointer, or any other
  // type of UB.
  EXPECT_OK(first_pub.Publish(first_message));

  proto::TestMessageString second_message;
  second_message.set_data("second_message");
  EXPECT_OK(second_pub.Publish(second_message));

  second_notification.WaitForNotificationWithTimeout(absl::Seconds(1));
  EXPECT_TRUE(second_notification.HasBeenNotified());
}

// The key-expression functions are only implemented in the "normal"
// (non-sanitizer) environment; the intraprocess-only imw stand-in does
// not implement these functions, so there is no sense testing them.

#if !defined(MEMORY_SANITIZER) && !defined(THREAD_SANITIZER) && \
    !defined(ADDRESS_SANITIZER)
TEST_P(PubSubTestSuite, TestKeyexprFuncs) {
  PubSub pubsub;
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("/foo"));
  EXPECT_EQ(false, pubsub.KeyexprIsCanon("/foo/"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo/bar"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo/bar/baz"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("*/bar/baz"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo/*/baz"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo/*/*"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("foo/bar/**"));
  EXPECT_EQ(false, pubsub.KeyexprIsCanon("foo/**/**"));
  EXPECT_EQ(true, pubsub.KeyexprIsCanon("**"));

  EXPECT_EQ(true, *pubsub.KeyexprIntersects("foo", "*"));
  EXPECT_EQ(true, *pubsub.KeyexprIntersects("*", "foo"));
  EXPECT_EQ(false, *pubsub.KeyexprIntersects("foo", "bar"));
  EXPECT_EQ(true, *pubsub.KeyexprIntersects("foo/*", "foo/bar"));
  EXPECT_EQ(false, *pubsub.KeyexprIntersects("foo/bar/*", "foo/bar"));

  EXPECT_EQ(true, *pubsub.KeyexprIncludes("*", "foo"));
  EXPECT_EQ(false, *pubsub.KeyexprIncludes("foo", "*"));
  EXPECT_EQ(false, *pubsub.KeyexprIncludes("*", "foo/bar"));
  EXPECT_EQ(true, *pubsub.KeyexprIncludes("**", "foo/bar"));
}
#endif

}  // namespace intrinsic
