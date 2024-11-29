// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_
#define INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_

#include <cstdint>
#include <functional>
#include <memory>
#include <string_view>
#include <type_traits>
#include <utility>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "google/protobuf/message.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"

namespace intrinsic {

class Queryable;

namespace internal {
// This is used internally as an implementation-independent callback mechanism.
// Users of the PubSub API will use QueryableCallback
using GeneralQueryableCallback =
    std::function<intrinsic_proto::pubsub::PubSubQueryResponse(
        const intrinsic_proto::pubsub::PubSubQueryRequest&)>;
struct QueryableLink {
  Queryable* queryable;
};

}  // namespace internal

class Queryable {
 public:
  Queryable() = default;
  Queryable(const Queryable&) = delete;
  Queryable& operator=(const Queryable&) = delete;

  Queryable(Queryable&& other)
      : key_(std::move(other.key_)),
        callback_(std::move(other.callback_)),
        link_(std::move(other.link_)) {
    link_->queryable = this;
  }
  Queryable& operator=(Queryable&& other) {
    key_ = std::move(other.key_);
    callback_ = std::move(other.callback_);
    link_ = std::move(other.link_);
    link_->queryable = this;
    return *this;
  }

  virtual ~Queryable();

  static absl::StatusOr<Queryable> Create(
      std::string_view key, internal::GeneralQueryableCallback callback);

  virtual intrinsic_proto::pubsub::PubSubQueryResponse Invoke(
      const intrinsic_proto::pubsub::PubSubQueryRequest& request_packet);

  std::string_view GetKey() { return key_; }

 private:
  Queryable(std::string_view key, internal::GeneralQueryableCallback callback)
      : key_(key),
        callback_(callback),
        link_(new internal::QueryableLink{.queryable = this}) {}
  std::string key_;
  internal::GeneralQueryableCallback callback_;

  std::unique_ptr<internal::QueryableLink> link_;
};

// This struct is passed to Queryable callbacks as first argument to pass
// additional context, e.g., tracing information.
struct QueryableContext {
  uint64_t trace_id;  // This can be used to keep tracing in a request
  uint64_t span_id;  // The parent span ID to associate calls in this request to
};

// Helper struct to deduce the types from the QueryableCallback lambda.
template <typename CallbackType>
struct QueryableCallbackTraits
    : public QueryableCallbackTraits<decltype(&CallbackType::operator())> {};

template <typename ClassType, typename RequestT, typename ResponseT>
struct QueryableCallbackTraits<absl::Status (ClassType::*)(
    const QueryableContext&, RequestT, ResponseT) const> {
  using RequestType = std::remove_cvref_t<RequestT>;
  using ResponseType = std::remove_cvref_t<ResponseT>;
  static_assert(std::is_const_v<std::remove_reference_t<RequestT>> &&
                    std::is_reference_v<RequestT>,
                "The request parameter needs to be a const reference.");
  static_assert(std::is_reference_v<ResponseT>,
                "The response parameter needs to be a reference.");
  static_assert(!std::is_const_v<std::remove_reference_t<ResponseT>>,
                "The response parameter needs cannot be a const argument.");
  static_assert(std::is_base_of_v<google::protobuf::Message, RequestType>,
                "First argument must be a proto message type");
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_
