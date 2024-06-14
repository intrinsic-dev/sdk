// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/pubsub.h"

#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>

#include <functional>
#include <memory>
#include <string_view>
#include <utility>

#include "absl/memory/memory.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/message.h"
#include "intrinsic/platform/pubsub/publisher.h"
#include "intrinsic/platform/pubsub/subscription.h"
#include "pybind11_abseil/no_throw_status.h"
#include "pybind11_abseil/status_casters.h"
#include "pybind11_protobuf/native_proto_caster.h"

namespace intrinsic {
namespace pubsub {

namespace {

absl::StatusOr<Subscription> CreateSubscriptionWithConfig(
    PubSub* self, absl::string_view topic, const TopicConfig& config,
    const google::protobuf::Message& exemplar, pybind11::object msg_callback,
    pybind11::object err_callback) {
  // The callback passed to the adapter must be able to be copied in a
  // separate thread without copying the msg_callback.
  // This allows the message callback to capture variables which
  // are not possible (or safe) to copy in a separate thread. This is the
  // case when the callback captures a python function, since those cannot
  // be copied without holding the GIL, and the adapter thread executing the
  // callback does not know to acquire the GIL. Using a shared pointer to
  // own the adapter callback satisfies these requirements.

  SubscriptionOkCallback<google::protobuf::Message> message_callback = {};
  SubscriptionErrorCallback error_callback = {};

  if (msg_callback && !msg_callback.is_none()) {
    message_callback = [py_msg_cb = std::move(msg_callback)](
                           const google::protobuf::Message& msg) {
      pybind11::gil_scoped_acquire gil;
      // This will create a copy in the py proto caster
      py_msg_cb(msg);
    };
  }

  if (err_callback && !err_callback.is_none()) {
    error_callback = [py_err_cb = std::move(err_callback)](
                         absl::string_view packet, absl::Status error) {
      pybind11::gil_scoped_acquire gil;
      py_err_cb(packet, pybind11::google::DoNotThrowStatus(error));
    };
  }

  return self->CreateSubscription(topic, config, exemplar,
                                  std::move(message_callback),
                                  std::move(error_callback));
}

absl::StatusOr<Subscription> CreateSubscription(
    PubSub* self, absl::string_view topic,
    const google::protobuf::Message& exemplar, pybind11::object msg_callback,
    pybind11::object err_callback) {
  return CreateSubscriptionWithConfig(self, topic, TopicConfig{}, exemplar,
                                      std::move(msg_callback),
                                      std::move(err_callback));
}

struct PySubscriptionDeleter {
  void operator()(Subscription* s) {
    // To avoid deadlock, the call to Zenoh.imw_destroy_subscription() needs to
    // happen with the GIL released. Otherwise, the GIL and the internal
    // callback mutex are potentially locked in opposite order by this thread
    // and the Zenoh callback thread pool, which can deadlock, especially on
    // high-frequency topics.
    {
      pybind11::gil_scoped_release release_gil;
      s->Unsubscribe();
    }

    // The Python GIL will be re-acquired now that the previous scoped_release
    // has disappeared. With the re-acquired GIL, we can safely delete the
    // subscription_data_ struct in Subscription, which contains the Python
    // callback object. A deadlock can no longer occur, because a message
    // callback will no longer occur because the remainder of the destruction
    // call chain is holding the GIL.
    delete s;
  }
};

}  // namespace

PYBIND11_MODULE(pubsub, m) {
  pybind11::google::ImportStatusModule();
  pybind11_protobuf::ImportNativeProtoCasters();

  pybind11::enum_<TopicConfig::TopicQoS>(m, "TopicQoS")
      .value("HighReliability", TopicConfig::TopicQoS::HighReliability)
      .value("Sensor", TopicConfig::TopicQoS::Sensor)
      .export_values();

  pybind11::class_<TopicConfig>(m, "TopicConfig")
      .def(pybind11::init<>())
      .def_readwrite("topic_qos", &TopicConfig::topic_qos);

  pybind11::class_<PubSub>(m, "PubSub")
      .def(pybind11::init<>())
      .def(pybind11::init<std::string_view>(),
           pybind11::arg("participant_name"))
      .def(pybind11::init<std::string_view, std::string_view>(),
           pybind11::arg("participant_name"), pybind11::arg("config"))
      // Cast required for overloaded methods:
      // https://pybind11.readthedocs.io/en/stable/classes.html#overloaded-methods
      .def("CreatePublisher", &PubSub::CreatePublisher, pybind11::arg("topic"),
           pybind11::arg("config") = TopicConfig{})
      .def("CreateSubscription", &CreateSubscriptionWithConfig,
           pybind11::arg("topic"), pybind11::arg("config"),
           pybind11::arg("exemplar"), pybind11::arg("msg_callback") = nullptr,
           pybind11::arg("error_callback") = nullptr)
      .def("CreateSubscription", &CreateSubscription, pybind11::arg("topic"),
           pybind11::arg("exemplar"), pybind11::arg("msg_callback") = nullptr,
           pybind11::arg("error_callback") = nullptr);

  pybind11::class_<Publisher>(m, "Publisher")
      .def("Publish",
           static_cast<absl::Status (Publisher::*)(
               const google::protobuf::Message&) const>(&Publisher::Publish),
           pybind11::arg("message"))
      .def("TopicName", &Publisher::TopicName);

  // The python GIL does not need to be locked during the entire destructor
  // of this class. Instead, the custom deleter provided during its
  // construction will acquite the GIL only during the deletion of the
  // SubscriptionData object, which holds the Python callback.
  pybind11::class_<Subscription,
                   std::unique_ptr<Subscription, PySubscriptionDeleter>>(
      m, "Subscription")
      .def("TopicName", &Subscription::TopicName);
}

}  // namespace pubsub
}  // namespace intrinsic
