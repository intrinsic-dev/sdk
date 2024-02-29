// Copyright 2023 Intrinsic Innovation LLC

#include <memory>
#include <string>
#include <utility>

#include "absl/strings/string_view.h"
#include "intrinsic/platform/pubsub/subscription.h"
#include "intrinsic/platform/pubsub/zenoh_subscription_data.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

namespace intrinsic {

Subscription::Subscription() = default;

Subscription::Subscription(absl::string_view topic_name,
                           std::unique_ptr<SubscriptionData> subscription_data)
    : topic_name_(topic_name),
      subscription_data_(std::move(subscription_data)) {}

Subscription::Subscription(Subscription &&) = default;

Subscription &Subscription::operator=(Subscription &&other) {
  if (!topic_name_.empty()) {
    Zenoh().imw_destroy_subscription(
        subscription_data_->prefixed_name.c_str(), zenoh_static_callback,
        subscription_data_->callback_functor.get());
  }
  topic_name_ = std::move(other.topic_name_);
  subscription_data_ = std::move(other.subscription_data_);
  return *this;
}

Subscription::~Subscription() {
  if (!topic_name_.empty()) {
    Zenoh().imw_destroy_subscription(
        subscription_data_->prefixed_name.c_str(), zenoh_static_callback,
        subscription_data_->callback_functor.get());
  }
}

}  // namespace intrinsic
