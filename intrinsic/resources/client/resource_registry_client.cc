// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/resources/client/resource_registry_client.h"

#include <iterator>
#include <memory>
#include <string>
#include <vector>

#include "absl/status/statusor.h"
#include "absl/strings/string_view.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "grpcpp/client_context.h"
#include "intrinsic/resources/proto/resource_registry.grpc.pb.h"
#include "intrinsic/resources/proto/resource_registry.pb.h"
#include "intrinsic/util/grpc/grpc.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic {
namespace resources {

absl::StatusOr<std::unique_ptr<ResourceRegistryClient>>
CreateResourceRegistryClient(absl::string_view grpc_address,
                             absl::Duration timeout,
                             absl::Duration connection_timeout) {
  INTR_ASSIGN_OR_RETURN(
      std::shared_ptr<grpc::Channel> channel,
      CreateClientChannel(grpc_address, absl::Now() + connection_timeout));
  return std::make_unique<ResourceRegistryClient>(
      intrinsic_proto::resources::ResourceRegistry::NewStub(channel), timeout);
}

absl::StatusOr<std::vector<intrinsic_proto::resources::ResourceInstance>>
ResourceRegistryClient::ListResources(
    const intrinsic_proto::resources::ListResourceInstanceRequest::StrictFilter
        &filter) const {
  std::vector<intrinsic_proto::resources::ResourceInstance> resource_instances;
  std::string page_token;
  auto deadline = absl::ToChronoTime(absl::Now() + timeout_);
  do {
    ::grpc::ClientContext context;
    context.set_deadline(deadline);
    intrinsic_proto::resources::ListResourceInstanceRequest req;
    intrinsic_proto::resources::ListResourceInstanceResponse resp;
    req.set_page_token(page_token);
    *req.mutable_strict_filter() = filter;
    INTR_RETURN_IF_ERROR(
        ToAbslStatus(stub_->ListResourceInstances(&context, req, &resp)));
    resource_instances.insert(resource_instances.end(),
                              std::make_move_iterator(resp.instances().begin()),
                              std::make_move_iterator(resp.instances().end()));
    page_token = resp.next_page_token();
  } while (!page_token.empty());

  return resource_instances;
}

absl::StatusOr<intrinsic_proto::resources::ResourceInstance>
ResourceRegistryClient::GetResource(absl::string_view name) const {
  ::grpc::ClientContext context;
  context.set_deadline(absl::ToChronoTime(absl::Now() + timeout_));

  intrinsic_proto::resources::GetResourceInstanceRequest req;
  intrinsic_proto::resources::ResourceInstance instance;
  req.set_name(name);
  INTR_RETURN_IF_ERROR(
      ToAbslStatus(stub_->GetResourceInstance(&context, req, &instance)));
  return instance;
}

}  // namespace resources
}  // namespace intrinsic
