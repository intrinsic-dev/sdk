// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_KVSTORE_H_
#define INTRINSIC_PLATFORM_PUBSUB_KVSTORE_H_

#include <functional>
#include <memory>
#include <string>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"

namespace intrinsic {

// Used to namespace a key in the KVStore. This is useful to prevent collisions.
// See go/intrinsic-kv-store for more details. If add_workcell_namespace is
// true, the workcell name will be added as a namespace. If
// add_solution_id_namespace is true, the solution id will be added as a
// namespace. If environment is set, the environment will be added as a
// namespace. If version is set, the version will be added as a namespace.
struct NamespaceConfig {
  bool add_workcell_namespace;
  bool add_solution_id_namespace;
  std::string environment;
  std::string version;
};

// Wildcard queries are used to query across multiple namespaces. For eg, if
// the workcell namespace is set to true, the key will be queried across all
// namespace values of workcells.
struct WildcardQueryConfig {
  bool workcell;
  bool solution_id;
  bool environment;
  bool version;
};

using KeyValueCallback =
    std::function<void(std::unique_ptr<google::protobuf::Any> value)>;

class KeyValueStore {
 public:
  // Sets the value for the given key. A key can't include any of the following
  // characters: /, *, ?, #, [ and ].
  absl::Status Set(absl::string_view key, const google::protobuf::Any& value,
                   const NamespaceConfig& config);

  // Returns the value for the given key. Wildcard queries are not supported
  // with this method, use the GetAll method instead. If wildcard queries are
  // sent, an error will be returned.
  absl::StatusOr<std::unique_ptr<google::protobuf::Any>> Get(
      absl::string_view key, const NamespaceConfig& config);

  // For a given key and WildcardQueryConfig, the KeyValueCallback will be
  // invoked for each key that matches the expression.
  absl::Status GetAll(absl::string_view key, const WildcardQueryConfig& config,
                      KeyValueCallback callback);
};

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_KVSTORE_H_