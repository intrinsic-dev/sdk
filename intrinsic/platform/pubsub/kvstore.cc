// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/platform/pubsub/kvstore.h"

#include <memory>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"

namespace intrinsic {

absl::Status KeyValueStore::Set(absl::string_view key,
                                const google::protobuf::Any& value,
                                const NamespaceConfig& config) {
  return absl::UnimplementedError("Not implemented");
}

absl::StatusOr<std::unique_ptr<google::protobuf::Any>> KeyValueStore::Get(
    absl::string_view key, const NamespaceConfig& config) {
  return absl::UnimplementedError("Not implemented");
}

absl::Status KeyValueStore::GetAll(absl::string_view keyexpr,
                                   const WildcardQueryConfig& config,
                                   KeyValueCallback callback) {
  return absl::UnimplementedError("Not implemented");
}

}  // namespace intrinsic
