// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBLISHER_DATA_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBLISHER_DATA_H_

#include <string>

namespace intrinsic {

struct PublisherData {
  std::string prefixed_name;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBLISHER_DATA_H_
