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

  // To handle complex cases, such as when unsubscribing from a Python topic,
  // the shutdown sequence may need to be done in delicate ordering to avoid the
  // potential for deadlock. The Python GIL needs to be acquired when the
  // callback is deleted, but the GIL needs to be released when the actual
  // Zenoh subscription is destroyed, due to internal mutex contention in the
  // callback thread pool.  Exposing the Unsubscribe() function allows a pybind
  // holder type to do this in the correct order.
  void Unsubscribe();

 private:
  std::string topic_name_;
  std::unique_ptr<SubscriptionData> subscription_data_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_SUBSCRIPTION_H_
