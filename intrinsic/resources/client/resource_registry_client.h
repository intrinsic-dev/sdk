// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_H_
#define INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_H_

#include <memory>
#include <utility>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/time.h"
#include "intrinsic/resources/client/resource_registry_client_interface.h"
#include "intrinsic/resources/proto/resource_registry.grpc.pb.h"
#include "intrinsic/resources/proto/resource_registry.pb.h"
#include "intrinsic/util/grpc/grpc.h"

namespace intrinsic {
namespace resources {

class ResourceRegistryClient;

// Creates a client that connects to the public resource registry service.
// Parameter connection_timeout is used when establishing the initial connection
// to the service. Parameter timeout is the timeout used for every request.
absl::StatusOr<std::unique_ptr<ResourceRegistryClient>>
CreateResourceRegistryClient(absl::string_view grpc_address,
                             absl::Duration timeout = absl::Seconds(60),
                             absl::Duration connection_timeout =
                                 intrinsic::kGrpcClientConnectDefaultTimeout);

// A client for the public resource registry service.
class ResourceRegistryClient : public ResourceRegistryClientInterface {
 public:
  explicit ResourceRegistryClient(
      std::unique_ptr<
          intrinsic_proto::resources::ResourceRegistry::StubInterface>
          stub,
      absl::Duration timeout)
      : stub_(std::move(stub)), timeout_(timeout) {}

  absl::StatusOr<std::vector<intrinsic_proto::resources::ResourceInstance>>
  ListResources(const intrinsic_proto::resources::ListResourceInstanceRequest::
                    StrictFilter &filter) const override;

  absl::StatusOr<intrinsic_proto::resources::ResourceInstance> GetResource(
      absl::string_view id) const override;

 private:
  std::unique_ptr<intrinsic_proto::resources::ResourceRegistry::StubInterface>
      stub_;
  const absl::Duration timeout_;
};

}  // namespace resources
}  // namespace intrinsic

#endif  // INTRINSIC_RESOURCES_CLIENT_RESOURCE_REGISTRY_CLIENT_H_
