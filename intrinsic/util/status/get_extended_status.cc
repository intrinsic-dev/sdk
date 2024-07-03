// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/get_extended_status.h"

#include <optional>
#include <string>
#include <utility>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "google/protobuf/any.pb.h"
#include "google/rpc/code.pb.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/support/status.h"
#include "intrinsic/util/proto/type_url.h"
#include "intrinsic/util/status/extended_status.pb.h"

namespace intrinsic {

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const absl::Status& status) {
  if (status.ok()) return std::nullopt;

  std::optional<absl::Cord> extended_status_payload = status.GetPayload(
      AddTypeUrlPrefix<intrinsic_proto::status::ExtendedStatus>());
  if (!extended_status_payload.has_value()) return std::nullopt;

  intrinsic_proto::status::ExtendedStatus es;
  if (!es.ParseFromCord(*extended_status_payload)) {
    LOG(WARNING) << "Failed to parse ExtendedStatus payload from status: "
                 << status;
    return std::nullopt;
  }

  return es;
}

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const google::rpc::Status& status) {
  if (status.code() == google::rpc::OK) return std::nullopt;

  const std::string extended_status_type_url =
      AddTypeUrlPrefix<intrinsic_proto::status::ExtendedStatus>();

  std::optional<intrinsic_proto::status::ExtendedStatus> extended_status;

  for (const google::protobuf::Any& detail_any : status.details()) {
    if (detail_any.type_url() == extended_status_type_url) {
      intrinsic_proto::status::ExtendedStatus es;
      if (detail_any.UnpackTo(&es)) {
        extended_status = std::move(es);
      }
    }
  }

  return extended_status;
}

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const grpc::Status& status) {
  if (status.ok()) return std::nullopt;

  if (status.error_details().empty()) {
    return std::nullopt;
  }

  google::rpc::Status rpc_status;
  if (!rpc_status.ParseFromString(status.error_details())) {
    return std::nullopt;
  }

  return GetExtendedStatus(rpc_status);
}

}  // namespace intrinsic
