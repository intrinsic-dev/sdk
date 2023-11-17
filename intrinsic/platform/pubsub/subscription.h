// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_SUBSCRIPTION_H_
#define INTRINSIC_PLATFORM_PUBSUB_SUBSCRIPTION_H_

#include <memory>
#include <string>

#include "absl/strings/string_view.h"

namespace intrinsic {

struct SubscriptionData;

class Subscription {
 public:
  Subscription();
  Subscription(absl::string_view topic_name,
               std::unique_ptr<SubscriptionData> subscription_data);

  ~Subscription();

  Subscription(const Subscription&) = delete;
  Subscription& operator=(const Subscription&) = delete;
  Subscription(Subscription&&);
  Subscription& operator=(Subscription&&);

  absl::string_view TopicName() const { return topic_name_; }

 private:
  std::string topic_name_ = {};
  std::unique_ptr<SubscriptionData> subscription_data_ = {};
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_SUBSCRIPTION_H_
