// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_PUBSUB_TEST_SUITE_H_
#define INTRINSIC_PLATFORM_PUBSUB_PUBSUB_TEST_SUITE_H_

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <functional>
#include <memory>

#include "intrinsic/platform/pubsub/pubsub.h"
#include "intrinsic/platform/test_utils/test_utils.h"

namespace intrinsic {

// This function must be provided for every adapter that is tested to be
// compliant with the PubSubAdapterInterface. The goal of this function is to
// allow the test suite to create an instance of the adapter. If the adapter
// requires a communication with a broker, this function must ensure that the
// adapter is connected to a broker;
using CreatePubSub =
    std::function<std::unique_ptr<PubSub>(std::shared_ptr<TestRuntimeContext>)>;

// A structure that includes all parameters that are passed into the suite test.
struct PubSubTestParams {
  // This is a function that starts an instance of a broker, if one is needed.
  SetupTestEnvironment create_broker;
};

class PubSubTestSuite : public testing::TestWithParam<PubSubTestParams> {
 public:
  void SetUp() override { context_ = GetParam().create_broker(); }

 protected:
  std::shared_ptr<TestRuntimeContext> context_;
  SubscriptionErrorCallback subscription_error_callback_fail_when_invoked_ =
      [](absl::string_view packet, const absl::Status& error) {
        ADD_FAILURE() << "SubscriptionErrorCallback was invoked but"
                         " wasn't supposed to be! The error was: "
                      << error.message();
      };
};

}  // namespace intrinsic
#endif  // INTRINSIC_PLATFORM_PUBSUB_PUBSUB_TEST_SUITE_H_
