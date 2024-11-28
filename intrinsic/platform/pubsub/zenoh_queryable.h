// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_QUERYABLE_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_QUERYABLE_H_

#include <functional>
#include <memory>
#include <string>
#include <type_traits>

#include "absl/status/statusor.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/platform/pubsub/adapters/pubsub.pb.h"
#include "intrinsic/platform/pubsub/queryable.h"

namespace intrinsic {

class ZenohQueryable : public Queryable {
 public:
  ZenohQueryable(std::string_view key,
                 internal::GeneralQueryableCallback callback)
      : key_(key), callback_(callback) {}
  ZenohQueryable(const ZenohQueryable&) = delete;
  ZenohQueryable(const ZenohQueryable&&) = default;
  ZenohQueryable& operator=(const ZenohQueryable&) = delete;
  ZenohQueryable& operator=(const ZenohQueryable&&) = default;

  ~ZenohQueryable() override;

  static absl::StatusOr<std::unique_ptr<ZenohQueryable>> Create(
      std::string_view key, internal::GeneralQueryableCallback callback);

  intrinsic_proto::pubsub::PubSubQueryResponse Invoke(
      const intrinsic_proto::pubsub::PubSubQueryRequest& request_packet)
      override;

 private:
  std::string key_;
  internal::GeneralQueryableCallback callback_;

  const char* GetKey() { return key_.c_str(); }
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_QUERYABLE_H_
