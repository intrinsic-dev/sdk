// Copyright 2023 Intrinsic Innovation LLC

#include <memory>
#include <string>
#include <utility>

#include "absl/time/time.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/message.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"
#include "intrinsic/platform/pubsub/publisher.h"
#include "intrinsic/platform/pubsub/publisher_stats.h"
#include "intrinsic/platform/pubsub/zenoh_publisher_data.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"
#include "intrinsic/util/proto_time.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

Publisher::Publisher(Publisher&&) = default;

Publisher& Publisher::operator=(Publisher&& other) {
  if (publisher_data_ && !publisher_data_->prefixed_name.empty()) {
    Zenoh().imw_destroy_publisher(publisher_data_->prefixed_name.c_str());
  }
  topic_name_ = std::move(other.topic_name_);
  publisher_data_ = std::move(other.publisher_data_);
  return *this;
}

Publisher::Publisher(absl::string_view topic_name,
                     std::unique_ptr<PublisherData> publisher_data)
    : topic_name_(topic_name), publisher_data_(std::move(publisher_data)) {}

Publisher::~Publisher() {
  if (publisher_data_ && !publisher_data_->prefixed_name.empty()) {
    Zenoh().imw_destroy_publisher(publisher_data_->prefixed_name.c_str());
  }
}

absl::Status Publisher::Publish(const google::protobuf::Message& message,
                                absl::Time event_time) const {
  intrinsic_proto::pubsub::PubSubPacket wrapper;
  wrapper.mutable_payload()->PackFrom(message);
  // When the pubsub message was sent out.
  absl::Time publish_time = absl::Now();
  INTR_ASSIGN_OR_RETURN(*wrapper.mutable_publish_time(), ToProto(publish_time));
  if (event_time > publish_time) {
    return absl::InvalidArgumentError("event_time should not be in the future");
  }

  imw_ret_t ret = Zenoh().imw_publish(publisher_data_->prefixed_name.c_str(),
                                      wrapper.SerializeAsString().c_str(),
                                      wrapper.ByteSizeLong());

  intrinsic::internal::PublisherStats::Singleton().Increment(topic_name_);

  if (ret != IMW_OK) {
    return absl::InternalError("Error publishing message");
  }
  return absl::OkStatus();
}

}  // namespace intrinsic
