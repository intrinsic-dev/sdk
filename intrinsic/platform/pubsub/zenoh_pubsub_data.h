// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBSUB_DATA_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBSUB_DATA_H_

#include <memory>
#include <string_view>

namespace intrinsic {

class PubSubData {
 public:
  explicit PubSubData(std::string_view config_param = std::string_view());

 private:
  class Session;
  std::shared_ptr<Session> session_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_PUBSUB_DATA_H_
