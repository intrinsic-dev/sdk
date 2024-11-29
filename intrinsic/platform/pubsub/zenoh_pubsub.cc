// Copyright 2023 Intrinsic Innovation LLC

#include <cstddef>
#include <memory>
#include <string>
#include <utility>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/match.h"
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/synchronization/notification.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"
#include "intrinsic/platform/pubsub/kvstore.h"
#include "intrinsic/platform/pubsub/publisher.h"
#include "intrinsic/platform/pubsub/pubsub.h"
#include "intrinsic/platform/pubsub/queryable.h"
#include "intrinsic/platform/pubsub/subscription.h"
#include "intrinsic/platform/pubsub/zenoh_publisher_data.h"
#include "intrinsic/platform/pubsub/zenoh_pubsub_data.h"
#include "intrinsic/platform/pubsub/zenoh_subscription_data.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_config.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {

constexpr char kIntrospectionTopicPrefix[] = "in/_introspection/";

std::string PubSubQoSToZenohQos(const TopicConfig::TopicQoS &qos) {
  return qos == TopicConfig::TopicQoS::Sensor ? "Sensor" : "HighReliability";
}

std::unique_ptr<PubSubData> MakePubSubData(
    absl::string_view config_param = absl::string_view()) {
  auto data = std::make_unique<PubSubData>();
  std::string config(config_param);
  if (config.empty()) {
    config = intrinsic::GetZenohPeerConfig();
    if (config.empty()) {
      LOG(FATAL) << "Could not get PubSub peer config";
    }
  }
  imw_ret_t ret = Zenoh().imw_init(config.c_str());
  if (ret != IMW_OK) {
    LOG(FATAL) << "Error creating a zenoh session with config " << config;
  }
  LOG(INFO) << "Created a zenoh session with libimw_zenoh version: "
            << Zenoh().imw_version();
  return data;
}

PubSub::PubSub() : data_(MakePubSubData()) {}

PubSub::PubSub(absl::string_view participant_name) : data_(MakePubSubData()) {}

PubSub::PubSub(absl::string_view participant_name, absl::string_view config)
    : data_(MakePubSubData(config)) {}

PubSub::~PubSub() { Zenoh().imw_fini(); }

absl::StatusOr<Publisher> PubSub::CreatePublisher(
    absl::string_view topic_name, const TopicConfig &config) const {
  auto prefixed_name = ZenohHandle::add_topic_prefix(topic_name);
  if (!prefixed_name.ok()) {
    return prefixed_name.status();
  }

  imw_ret_t ret = Zenoh().imw_create_publisher(
      prefixed_name->c_str(),
      intrinsic::PubSubQoSToZenohQos(config.topic_qos).c_str());

  if (ret == IMW_ERROR) {
    return absl::InternalError("Error creating a publisher");
  }
  auto publisher_data = std::make_unique<PublisherData>();
  publisher_data->prefixed_name = *prefixed_name;
  return Publisher(topic_name, std::move(publisher_data));
}

absl::StatusOr<Subscription> PubSub::CreateSubscription(
    absl::string_view topic_name, const TopicConfig &config,
    SubscriptionOkCallback<intrinsic_proto::pubsub::PubSubPacket> msg_callback)
    const {
  auto prefixed_name = ZenohHandle::add_topic_prefix(topic_name);
  if (!prefixed_name.ok()) {
    return prefixed_name.status();
  }

  auto subscription_data = std::make_unique<SubscriptionData>();
  subscription_data->prefixed_name = *prefixed_name;
  auto callback = std::make_unique<imw_callback_functor_t>(
      [msg_callback](const char *keyexpr, const void *blob,
                     const size_t blob_len) {
        // Don't attempt to deserialize the introspection data
        // since it's JSON and doesn't need to be logged anyway;
        // it will be parsed and captured by Prometheus separately
        if (absl::StartsWith(keyexpr, kIntrospectionTopicPrefix)) return;

        intrinsic_proto::pubsub::PubSubPacket msg;
        bool success = msg.ParseFromArray(blob, blob_len);
        if (!success) {
          LOG_EVERY_N(ERROR, 1)
              << absl::StrFormat("Deserializing message failed. Topic: ")
              << keyexpr;
          return;
        }
        msg_callback(msg);
      });
  subscription_data->callback_functor = std::move(callback);

  imw_ret_t ret = Zenoh().imw_create_subscription(
      prefixed_name->c_str(), zenoh_static_callback,
      intrinsic::PubSubQoSToZenohQos(config.topic_qos).c_str(),
      subscription_data->callback_functor.get());
  if (ret != IMW_OK) {
    return absl::InternalError("Error creating a subscription");
  }
  return Subscription(topic_name, std::move(subscription_data));
}
absl::StatusOr<Subscription> PubSub::CreateSubscription(
    absl::string_view topic_name, const TopicConfig &config,
    SubscriptionOkExpandedCallback<intrinsic_proto::pubsub::PubSubPacket>
        msg_callback) const {
  auto prefixed_name = ZenohHandle::add_topic_prefix(topic_name);
  if (!prefixed_name.ok()) {
    return prefixed_name.status();
  }

  auto subscription_data = std::make_unique<SubscriptionData>();
  subscription_data->prefixed_name = *prefixed_name;
  auto callback = std::make_unique<imw_callback_functor_t>(
      [msg_callback](const char *keyexpr, const void *blob,
                     const size_t blob_len) {
        absl::string_view topic_str(keyexpr);
        if (absl::StartsWith(topic_str, kIntrospectionTopicPrefix)) return;

        intrinsic_proto::pubsub::PubSubPacket msg;
        bool success = msg.ParseFromArray(blob, blob_len);
        if (!success) {
          LOG_EVERY_N(ERROR, 1) << absl::StrFormat(
              "Deserializing message failed. Topic: %s", keyexpr);
          return;
        }
        auto topic_name = ZenohHandle::remove_topic_prefix(keyexpr);
        if (!topic_name.ok()) {
          LOG_EVERY_N(ERROR, 1) << "Topic name error: " << topic_name.status();
          return;
        }
        msg_callback(*topic_name, msg);
      });
  subscription_data->callback_functor = std::move(callback);

  imw_ret_t ret = Zenoh().imw_create_subscription(
      prefixed_name->c_str(), zenoh_static_callback,
      intrinsic::PubSubQoSToZenohQos(config.topic_qos).c_str(),
      subscription_data->callback_functor.get());
  if (ret != IMW_OK) {
    return absl::InternalError("Error creating a subscription");
  }
  return Subscription(topic_name, std::move(subscription_data));
}

bool PubSub::KeyexprIsCanon(absl::string_view keyexpr) const {
  const auto prefixed_keyexpr = ZenohHandle::add_topic_prefix(keyexpr);
  if (!prefixed_keyexpr.ok()) return false;
  return Zenoh().imw_keyexpr_is_canon(prefixed_keyexpr->c_str()) == 0;
}

absl::StatusOr<bool> PubSub::KeyexprIntersects(absl::string_view left,
                                               absl::string_view right) const {
  INTR_ASSIGN_OR_RETURN(const std::string prefixed_left,
                        ZenohHandle::add_topic_prefix(left));
  INTR_ASSIGN_OR_RETURN(const std::string prefixed_right,
                        ZenohHandle::add_topic_prefix(right));
  const int result = Zenoh().imw_keyexpr_intersects(prefixed_left.c_str(),
                                                    prefixed_right.c_str());
  switch (result) {
    case 0:
      return true;
    case 1:
      return false;
    default:
      return absl::InvalidArgumentError("A key expression is invalid");
  }
}

absl::StatusOr<bool> PubSub::KeyexprIncludes(absl::string_view left,
                                             absl::string_view right) const {
  INTR_ASSIGN_OR_RETURN(const std::string prefixed_left,
                        ZenohHandle::add_topic_prefix(left));
  INTR_ASSIGN_OR_RETURN(const std::string prefixed_right,
                        ZenohHandle::add_topic_prefix(right));
  const int result = Zenoh().imw_keyexpr_includes(prefixed_left.c_str(),
                                                  prefixed_right.c_str());
  switch (result) {
    case 0:
      return true;
    case 1:
      return false;
    default:
      return absl::InvalidArgumentError("A key expression is invalid");
  }
}

absl::StatusOr<intrinsic::KeyValueStore> PubSub::KeyValueStore() const {
  return intrinsic::KeyValueStore();
}

namespace {
struct GetOneData {
  absl::Notification notification;
  absl::StatusOr<intrinsic_proto::pubsub::PubSubQueryResponse> response_packet;
};

void GetOneCallbackFn(const char *key, const void *response_bytes,
                      const size_t response_bytes_len, void *user_context) {
  GetOneData *query_data = static_cast<GetOneData *>(user_context);
  std::string_view response_str(static_cast<const char *>(response_bytes),
                                response_bytes_len);
  intrinsic_proto::pubsub::PubSubQueryResponse response_packet;
  if (!response_packet.ParseFromString(response_str)) {
    query_data->response_packet =
        absl::InvalidArgumentError("Failed to parse response packet");
  }
  query_data->response_packet = std::move(response_packet);
}

void GetOneOnDoneCallbackFn(const char *key, void *user_context) {
  GetOneData *query_data = static_cast<GetOneData *>(user_context);
  query_data->notification.Notify();
}

}  // namespace

bool PubSub::SupportsQueryables() const { return true; }

absl::StatusOr<Queryable> PubSub::CreateQueryableImpl(
    absl::string_view key, internal::GeneralQueryableCallback callback) {
  return Queryable::Create(key, callback);
}

absl::StatusOr<intrinsic_proto::pubsub::PubSubQueryResponse> PubSub::GetOneImpl(
    absl::string_view key,
    const intrinsic_proto::pubsub::PubSubQueryRequest &request,
    const QueryOptions &options) {
  std::string serialized_request = request.SerializeAsString();
  GetOneData query_data;
  if (Zenoh().imw_query(key.data(), &GetOneCallbackFn, &GetOneOnDoneCallbackFn,
                        serialized_request.c_str(), serialized_request.size(),
                        &query_data) != IMW_OK) {
    return absl::InternalError(
        absl::StrFormat("Executing query for key '%s' failed", key));
  }

  query_data.notification.WaitForNotification();

  return query_data.response_packet;
}

}  // namespace intrinsic
