// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/cc_client/client.h"

#include <algorithm>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/robot_config.h"
#include "intrinsic/icon/common/part_properties.h"
#include "intrinsic/icon/proto/service.grpc.pb.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/icon/proto/types.pb.h"
#include "intrinsic/icon/release/grpc_time_support.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/grpc/channel_interface.h"
#include "intrinsic/util/proto_time.h"

namespace intrinsic {
namespace icon {

Client::Client(std::shared_ptr<ChannelInterface> icon_channel)
    : channel_(icon_channel),
      stub_(
          intrinsic_proto::icon::IconApi::NewStub(icon_channel->GetChannel())),
      timeout_(kClientDefaultTimeout),
      client_context_factory_(icon_channel->GetClientContextFactory()) {}

Client::Client(
    std::unique_ptr<intrinsic_proto::icon::IconApi::StubInterface> stub,
    ClientContextFactory client_context_factory)
    : channel_(nullptr),
      stub_(std::move(stub)),
      timeout_(kClientDefaultTimeout),
      client_context_factory_(std::move(client_context_factory)) {}

absl::StatusOr<intrinsic_proto::icon::ActionSignature>
Client::GetActionSignatureByName(absl::string_view action_type_name) const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetActionSignatureByNameRequest request;
  request.set_name(std::string(action_type_name));
  intrinsic_proto::icon::GetActionSignatureByNameResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->GetActionSignatureByName(context.get(), request, &response));
  if (!response.has_action_signature()) {
    return absl::NotFoundError(
        absl::StrCat("Could not get action signature: action type \"",
                     action_type_name, "\" not found."));
  }
  return response.action_signature();
}

absl::StatusOr<RobotConfig> Client::GetConfig() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetConfigRequest request;
  intrinsic_proto::icon::GetConfigResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->GetConfig(context.get(), request, &response));
  return RobotConfig(response);
}

absl::StatusOr<intrinsic_proto::icon::GetStatusResponse> Client::GetStatus()
    const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetStatusRequest request;
  intrinsic_proto::icon::GetStatusResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->GetStatus(context.get(), request, &response));
  return response;
}

absl::StatusOr<intrinsic_proto::icon::PartStatus> Client::GetSinglePartStatus(
    absl::string_view part_name) const {
  INTRINSIC_ASSIGN_OR_RETURN(
      intrinsic_proto::icon::GetStatusResponse robot_status, GetStatus());
  auto part_status_it = robot_status.part_status().find(std::string(part_name));
  if (part_status_it == robot_status.part_status().end()) {
    return absl::NotFoundError(
        absl::StrCat("Robot status does not contain Part status for Part '",
                     part_name, "'"));
  }
  return part_status_it->second;
}

absl::Status Client::RestartServer() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  google::protobuf::Empty resp;
  return stub_->RestartServer(context.get(), {}, &resp);
}

absl::StatusOr<bool> Client::IsActionCompatible(
    absl::string_view part_name, absl::string_view action_type_name) const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::IsActionCompatibleRequest request;
  request.set_part_name(std::string(part_name));
  request.set_action_type_name(std::string(action_type_name));
  intrinsic_proto::icon::IsActionCompatibleResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->IsActionCompatible(context.get(), request, &response));
  return response.is_compatible();
}

absl::StatusOr<bool> Client::IsActionCompatible(
    const SlotPartMap& slot_part_map,
    absl::string_view action_type_name) const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::IsActionCompatibleRequest request;
  *request.mutable_slot_part_map() = ToProto(slot_part_map);
  request.set_action_type_name(std::string(action_type_name));
  intrinsic_proto::icon::IsActionCompatibleResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->IsActionCompatible(context.get(), request, &response));
  return response.is_compatible();
}

absl::StatusOr<std::vector<intrinsic_proto::icon::ActionSignature>>
Client::ListActionSignatures() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::ListActionSignaturesRequest request;
  intrinsic_proto::icon::ListActionSignaturesResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->ListActionSignatures(context.get(), request, &response));
  std::vector<intrinsic_proto::icon::ActionSignature> out(
      response.action_signatures().begin(), response.action_signatures().end());
  std::sort(
      out.begin(), out.end(),
      [](const intrinsic_proto::icon::ActionSignature& a,
         const intrinsic_proto::icon::ActionSignature& b) {
        if ((&a != &b) && (a.action_type_name() == b.action_type_name())) {
          LOG(WARNING) << "Server returned duplicate action type name \""
                       << a.action_type_name() << "\"";
        }
        return a.action_type_name() < b.action_type_name();
      });
  return out;
}

absl::StatusOr<std::vector<std::string>> Client::ListCompatibleParts(
    absl::Span<const std::string> action_type_names) const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::ListCompatiblePartsRequest request;
  *request.mutable_action_type_names() = {action_type_names.begin(),
                                          action_type_names.end()};
  intrinsic_proto::icon::ListCompatiblePartsResponse response;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->ListCompatibleParts(context.get(), request, &response));
  return std::vector<std::string>(response.parts().begin(),
                                  response.parts().end());
}

absl::StatusOr<std::vector<std::string>> Client::ListParts() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::ListPartsResponse response;
  INTRINSIC_RETURN_IF_ERROR(stub_->ListParts(
      context.get(), intrinsic_proto::icon::ListPartsRequest(), &response));
  return std::vector<std::string>(response.parts().begin(),
                                  response.parts().end());
}

absl::Status Client::Enable() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::EnableRequest req;
  intrinsic_proto::icon::EnableResponse resp;
  return stub_->Enable(context.get(), req, &resp);
}

absl::Status Client::Disable() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::DisableRequest req;
  intrinsic_proto::icon::DisableResponse resp;
  return stub_->Disable(context.get(), req, &resp);
}

absl::Status Client::ClearFaults() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::ClearFaultsRequest req;
  intrinsic_proto::icon::ClearFaultsResponse resp;
  return stub_->ClearFaults(context.get(), req, &resp);
}

absl::StatusOr<OperationalStatus> Client::GetOperationalStatus() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetOperationalStatusRequest req;
  intrinsic_proto::icon::GetOperationalStatusResponse resp;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->GetOperationalStatus(context.get(), req, &resp));
  return FromProto(resp.operational_status());
}

absl::Status Client::SetSpeedOverride(double new_speed_override) {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::SetSpeedOverrideRequest req;
  req.set_override_factor(new_speed_override);
  intrinsic_proto::icon::SetSpeedOverrideResponse resp;
  return stub_->SetSpeedOverride(context.get(), req, &resp);
}

absl::StatusOr<double> Client::GetSpeedOverride() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetSpeedOverrideResponse resp;
  INTRINSIC_RETURN_IF_ERROR(stub_->GetSpeedOverride(
      context.get(), intrinsic_proto::icon::GetSpeedOverrideRequest(), &resp));
  return resp.override_factor();
}

absl::Status Client::SetPartProperties(
    const PartPropertyMap& property_map) const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::SetPartPropertiesRequest req;
  for (const auto& [part_name, properties] : property_map.properties) {
    intrinsic_proto::icon::PartPropertyValues part_properties_proto;
    for (const auto& [property_name, property_value] : properties) {
      part_properties_proto.mutable_property_values_by_name()->insert(
          {property_name, ToProto(property_value)});
    }
    req.mutable_part_properties_by_part_name()->insert(
        {part_name, std::move(part_properties_proto)});
  }
  intrinsic_proto::icon::SetPartPropertiesResponse resp;
  return stub_->SetPartProperties(context.get(), req, &resp);
}

absl::StatusOr<TimestampedPartProperties> Client::GetPartProperties() const {
  std::unique_ptr<::grpc::ClientContext> context = client_context_factory_();
  context->set_deadline(::grpc::DeadlineFromDuration(timeout_));
  intrinsic_proto::icon::GetPartPropertiesRequest req;
  intrinsic_proto::icon::GetPartPropertiesResponse resp;
  INTRINSIC_RETURN_IF_ERROR(
      stub_->GetPartProperties(context.get(), req, &resp));
  TimestampedPartProperties properties;
  INTRINSIC_ASSIGN_OR_RETURN(properties.timestamp_wall,
                             intrinsic::FromProto(resp.timestamp_wall()));
  properties.timestamp_control = intrinsic::FromProto(resp.timestamp_control());

  for (const auto& [part_name, properties_proto] :
       resp.part_properties_by_part_name()) {
    for (const auto& [property_name, property_value_proto] :
         properties_proto.property_values_by_name()) {
      INTRINSIC_ASSIGN_OR_RETURN(
          properties.properties[part_name][property_name],
          FromProto(property_value_proto));
    }
  }

  return properties;
}

}  // namespace icon
}  // namespace intrinsic
