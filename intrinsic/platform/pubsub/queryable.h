// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_
#define INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_

#include <cstdint>
#include <functional>
#include <type_traits>

#include "absl/status/statusor.h"
#include "google/protobuf/message.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"

namespace intrinsic {

class Queryable {
 public:
  virtual ~Queryable() = default;

  // This can be used for mocking/testing
  virtual intrinsic_proto::pubsub::PubSubQueryResponse Invoke(
      const intrinsic_proto::pubsub::PubSubQueryRequest& request_packet) = 0;
};

struct QueryableContext {
  uint64_t trace_id;  // This can be used to keep tracing in a request
  uint64_t span_id;  // The parent span ID to associate calls in this request to
};

template <typename RequestT, typename ResponseT,
          typename = std::enable_if_t<
              std::is_base_of_v<google::protobuf::Message, RequestT>>,
          typename = std::enable_if_t<
              std::is_base_of_v<google::protobuf::Message, ResponseT>>>
using QueryableCallback = std::function<absl::StatusOr<ResponseT>(
    const QueryableContext& context, const RequestT& request)>;

namespace internal {
// This is used internally as an implementation-independent callback mechanism.
// Users of the PubSub API will use QueryableCallback
using GeneralQueryableCallback =
    std::function<intrinsic_proto::pubsub::PubSubQueryResponse(
        const intrinsic_proto::pubsub::PubSubQueryRequest&)>;
}  // namespace internal

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_QUERYABLE_H_
