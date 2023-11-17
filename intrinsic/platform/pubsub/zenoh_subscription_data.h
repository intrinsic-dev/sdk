// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_SUBSCRIPTION_DATA_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_SUBSCRIPTION_DATA_H_

#include <memory>
#include <string>

#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

namespace intrinsic {

struct SubscriptionData {
  std::unique_ptr<imw_callback_functor_t> callback_functor;
  std::string prefixed_name;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_SUBSCRIPTION_DATA_H_
