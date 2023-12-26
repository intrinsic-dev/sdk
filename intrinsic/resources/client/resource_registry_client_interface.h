// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_INTERFACE_H_
#define INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_INTERFACE_H_

#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "intrinsic/resources/proto/resource_registry.pb.h"

namespace intrinsic {
namespace resources {

// A client interface for the public resource registry service.
class ResourceRegistryClientInterface {
 public:
  virtual ~ResourceRegistryClientInterface() = default;

  virtual absl::StatusOr<
      std::vector<intrinsic_proto::resources::ResourceInstance>>
  ListResources(const intrinsic_proto::resources::ListResourceInstanceRequest::
                    StrictFilter &filter) const = 0;

  virtual absl::StatusOr<intrinsic_proto::resources::ResourceInstance>
  GetResource(absl::string_view id) const = 0;
};

}  // namespace resources
}  // namespace intrinsic

#endif  // INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_INTERFACE_H_
