// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_PUBSUB_H_
#define INTRINSIC_PLATFORM_PUBSUB_PUBSUB_H_

#include <functional>
#include <memory>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "google/protobuf/any.pb.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"
#include "intrinsic/platform/pubsub/publisher.h"
#include "intrinsic/platform/pubsub/subscription.h"

// The PubSub class implements an interface to a publisher-subscriber
// system, a one-to-many communication bus that allows sending protocol buffers
// across a non-real-time context with a relatively low-latency.
// Subscribers receive messages published to a topic serially in the order
// that they were published. A Subscriber may receive messages published to a
// topic before the time of subscription.
//
// Creating a PubSub client:
//
//   #include "intrinsic/platform/pubsub/pubsub.h"
//
//   PubSub pubsub;
//
// Publishing a message (see go/intrinsic-dds-topic-naming-design for naming
// convention):
//
//   INTRINSIC_ASSIGN_OR_RETURN(auto publisher,
//                     pubsub->CreatePublisher(response_topic, TopicConfig()));
//   TestMessage message;
//   INTRINSIC_RETURN_IF_ERROR(publisher.Publish("/test/my_topic", message));
//
// Note: Be careful to not destroy the PubSub instance after creating a
// Publisher.
//
// Creating a Subscription to a topic:
//
//   INTRINSIC_ASSIGN_OR_RETURN(
//      auto sub,
//      pubsub.CreateSubscription<proto::TestMessage>("/test/my_topic",
//         [](const TestMessage& message) {
//           // Here we process the received message.
//         },
//         [](absl::string_view packet, absl::Status error) {
//           // Here we handle receiving of an invalid message (Unimplemented).
//      });
// Note: Be careful to not destroy the PubSub instance after creating a
// Subscription.
//
namespace intrinsic {

struct TopicConfig {
  enum TopicQoS {
    Sensor = 0,
    HighReliability = 1,
  };

  TopicQoS topic_qos = HighReliability;
};

// The following two callbacks are defined to be used asynchronously when a
// message arrives on a topic that a subscription was requested to.
//
// SubscriptionOkCallback is called whenever a valid message is received. This
// callback returns typed message.
template <typename T>
using SubscriptionOkCallback = std::function<void(const T& message)>;

template <typename T>
using SubscriptionOkExpandedCallback =
    std::function<void(absl::string_view topic, const T& message)>;

// SubscriptionErrorCallback is called whenever a message is received on a
// subscribed topic but the message could not be parsed or converted to the
// desired type. This function returns the raw value of the received packet and
// status error indicating the problem.
using SubscriptionErrorCallback =
    std::function<void(absl::string_view packet, absl::Status error)>;

struct PubSubData;

// This class is thread-safe.
class PubSub {
 public:
  PubSub();
  explicit PubSub(absl::string_view participant_name);
  explicit PubSub(absl::string_view participant_name, absl::string_view config);

  PubSub(const PubSub&) = delete;
  PubSub& operator=(const PubSub&) = delete;
  PubSub(PubSub&&) = default;
  PubSub& operator=(PubSub&&) = default;
  ~PubSub();

  absl::StatusOr<Publisher> CreatePublisher(absl::string_view topic,
                                            const TopicConfig& config) const;

  // Creates a subscription which invokes the specified callback when a package
  // is received on the topic. This function can only be invoked for proto
  // messages but not for google::protobuf::Message itself.
  //
  // Example 1: Creating a subscription where a lambda is passed in requires
  //   the caller to explicitly specify the template parameter T since it cannot
  //   be deduced from the lambda.
  //
  // PubSub pubsub;
  // INTRINSIC_ASSIGN_OR_RETURN(auto subscription,
  // pubsub.CreateSubscription<MyProto>(
  //   "some/topic", {}, [](const MyProto& my_proto){}));
  //
  // Example 2: Creating a subscription from a std::function allows us to
  //   automatically deduce the template parameter T.
  //
  // std::function<void(const MyProto&)> callback = [](const MyProto&){};
  // PubSub pubsub;
  // INTRINSIC_ASSIGN_OR_RETURN(auto subscription, pubsub.CreateSubscription(
  //   "some/topic", {}, callback));
  template <typename T>
  absl::StatusOr<Subscription> CreateSubscription(
      absl::string_view topic, const TopicConfig& config,
      SubscriptionOkCallback<T> msg_callback,
      SubscriptionErrorCallback error_callback = {}) const {
    static_assert(!std::is_same_v<google::protobuf::Message, T>,
                  "The wrong overload has been called. Please use the "
                  "CreateSubscription() overload which takes an exemplar (a "
                  "sample message) during its call.");
    return CreateSubscription(topic, config, T::default_instance(),
                              std::move(msg_callback),
                              std::move(error_callback));
  }

  // Creates a subscription using an exemplar, i.e. a sample proto message.
  //
  // This function requires an exemplar (a sample message) to be passed in
  // which can hold the payload of a PubSubPacket. The exemplar is used during
  // each callback to create a new proto message, to extract the payload from
  // the PubSubPacket and it is then passed to the actual callback function.
  template <typename T>
  absl::StatusOr<Subscription> CreateSubscription(
      absl::string_view topic, const TopicConfig& config, const T& exemplar,
      SubscriptionOkCallback<T> msg_callback,
      SubscriptionErrorCallback error_callback = {}) const {
    static_assert(std::is_base_of_v<google::protobuf::Message, T>,
                  "Protocol buffers are the only supported serialization "
                  "format for PubSub.");

    // This payload is shared between callbacks and may be read from multiple
    // threads. We need a shared_ptr here because a std::function must be
    // copyable.
    std::shared_ptr<T> shared_payload(exemplar.New());

    // The message callback is never copied. It is merely moved to this helper
    // lambda which is itself moved to the subscription class.
    auto package_to_payload =
        [callback = std::move(msg_callback),
         error_callback = std::move(error_callback),
         shared_payload = std::move(shared_payload)](
            const intrinsic_proto::pubsub::PubSubPacket& packet) {
          // Create a local copy of the shared payload which we can safely
          // modify in different threads.
          std::unique_ptr<T> payload(shared_payload->New());
          if (!packet.payload().UnpackTo(payload.get())) {
            HandleError(error_callback, packet, *payload);
            return;
          }
          callback(*payload);
        };
    return CreateSubscription(topic, config, std::move(package_to_payload));
  }

  // Creates a subscription for a raw PubSubPacket. This kind of subscription is
  // useful for filtering packets or processing them otherwise without the need
  // to deserialize the data.
  absl::StatusOr<Subscription> CreateSubscription(
      absl::string_view topic, const TopicConfig& config,
      SubscriptionOkCallback<intrinsic_proto::pubsub::PubSubPacket>
          msg_callback) const;

  absl::StatusOr<Subscription> CreateSubscription(
      absl::string_view topic, const TopicConfig& config,
      SubscriptionOkExpandedCallback<intrinsic_proto::pubsub::PubSubPacket>
          msg_callback) const;

  // Test if a key expression is "canonical", meaning that it has a valid
  // combination of wildcards, no illegal characters, no trailing slash, etc.
  bool KeyexprIsCanon(absl::string_view keyexpr) const;

  // Test if a key expression intersects another key expression. Helpful when
  // wildcards are involved and this becomes a non-trivial calculation.
  // Returns an error if any input is non-canonical.
  absl::StatusOr<bool> KeyexprIntersects(absl::string_view left,
                                         absl::string_view right) const;

  // Test if a key expression includes all keys of another key expression.
  // Helpful when wildcards are involved and this becomes non-trivial.
  // Returns an error if any input is non-canonical.
  absl::StatusOr<bool> KeyexprIncludes(absl::string_view left,
                                       absl::string_view right) const;

 private:
  static void HandleError(const SubscriptionErrorCallback& error_callback,
                          const intrinsic_proto::pubsub::PubSubPacket& packet,
                          const google::protobuf::Message& payload) {
    if (error_callback == nullptr) {
      LOG(ERROR) << (packet.DebugString(),
                     absl::InvalidArgumentError(absl::StrCat(
                         "Expected payload of type ", payload.GetTypeName(),
                         " but got ", packet.payload().type_url())));
      return;
    }
    error_callback(packet.DebugString(),
                   absl::InvalidArgumentError(absl::StrCat(
                       "Expected payload of type ", payload.GetTypeName(),
                       " but got ", packet.payload().type_url())));
  }

  // We use a shared_ptr here because it allows us to auto generate the
  // destructor even when PubSubData is an incomplete type.
  std::shared_ptr<PubSubData> data_;
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_PUBSUB_H_
