// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/zenoh_queryable.h"

#include <cstddef>
#include <memory>
#include <string>
#include <string_view>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/str_format.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"
#include "intrinsic/platform/pubsub/queryable.h"
#include "intrinsic/platform/pubsub/zenoh_util/zenoh_handle.h"

namespace intrinsic {

namespace {

// imw_queryable_callback_fn
static void ZenohQueryableCallback(const char* key, const void* query_bytes,
                                   const size_t query_bytes_len,
                                   const void* query_context,
                                   void* user_context) {
  // Decode query
  intrinsic_proto::pubsub::PubSubQueryRequest request_packet;
  if (!request_packet.ParseFromArray(query_bytes, query_bytes_len)) {
    LOG(ERROR) << absl::StrFormat(
        "Deserializing message failed for query. Key: %s", key);
    return;
  }

  ZenohQueryable* queryable = static_cast<ZenohQueryable*>(user_context);
  intrinsic_proto::pubsub::PubSubQueryResponse response_packet =
      queryable->Invoke(request_packet);

  // Encode and send response
  std::string reply_message;
  if (!response_packet.SerializeToString(&reply_message)) {
    LOG(ERROR) << absl::StrFormat(
        "Failed to serialize response message for key '%s'", key);
    return;
  }
  if (Zenoh().imw_queryable_reply(query_context, key, reply_message.c_str(),
                                  reply_message.size()) != IMW_OK) {
    LOG(ERROR) << absl::StrFormat("Failed to send reply message for key '%s'",
                                  key);
  }
}

}  // namespace

absl::StatusOr<std::unique_ptr<ZenohQueryable>> ZenohQueryable::Create(
    std::string_view key, internal::GeneralQueryableCallback callback) {
  auto queryable = std::make_unique<ZenohQueryable>(key, callback);
  if (imw_ret_t rv = Zenoh().imw_create_queryable(
          queryable->GetKey(), &ZenohQueryableCallback, queryable.get());
      rv != IMW_OK) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Failed to create queryable for key '%s' (code %d)", key, rv));
  }
  return queryable;
}

ZenohQueryable::~ZenohQueryable() {
  if (Zenoh().imw_destroy_queryable(GetKey(), &ZenohQueryableCallback, this) !=
      IMW_OK) {
    LOG(ERROR) << absl::StrFormat("Failed to destroy queryable for '%s'", key_);
  }
}

intrinsic_proto::pubsub::PubSubQueryResponse ZenohQueryable::Invoke(
    const intrinsic_proto::pubsub::PubSubQueryRequest& request_packet) {
  return callback_(request_packet);
}

}  // namespace intrinsic
