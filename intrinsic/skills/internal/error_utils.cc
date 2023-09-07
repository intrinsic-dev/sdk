// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/skills/internal/error_utils.h"

#include <optional>
#include <string>
#include <utility>

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "grpcpp/support/error_details.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/skills/proto/error.pb.h"

namespace intrinsic {
namespace skills {

absl::Status ToAbslStatus(const ::grpc::Status& grpc_status) {
  // Note: doing the absl_status = grpc_status assignment attempts to interpret
  // the error_details in a certain way, so we bypass the assignment in favor
  // of our own translation for clarity and to avoid sneaky bugs.
  absl::Status out(static_cast<absl::StatusCode>(grpc_status.error_code()),
                   grpc_status.error_message());

  // The error_details field should be a serialized google.rpc.Status.
  google::rpc::Status status;
  intrinsic_proto::skills::SkillErrorInfo error_info;
  // Assume the error came from grpc if not specified.
  error_info.set_error_type(
      intrinsic_proto::skills::SkillErrorInfo::ERROR_TYPE_GRPC);
  if (status.ParseFromString(grpc_status.error_details())) {
    // Look through the details for the first proto that can be unpacked as a
    // SkillErrorInfo.
    for (const auto& any : status.details()) {
      intrinsic_proto::skills::SkillErrorInfo try_unpack;
      if (any.UnpackTo(&try_unpack)) {
        error_info = std::move(try_unpack);
        break;
      }
    }
  }
  SetErrorInfo(error_info, out);

  return out;
}

::grpc::Status ToGrpcStatus(
    const absl::Status& absl_status,
    const intrinsic_proto::skills::SkillErrorInfo& error_info) {
  ::google::rpc::Status my_status = ToGoogleRpcStatus(absl_status, error_info);
  ::grpc::Status out;
  // Should only fail if out is nullptr.
  CHECK_OK(grpc::SetErrorDetails(my_status, &out));
  return out;
}

::google::rpc::Status ToGoogleRpcStatus(
    const absl::Status& absl_status,
    const intrinsic_proto::skills::SkillErrorInfo& error_info) {
  ::google::rpc::Status my_status;
  my_status.set_code(static_cast<int>(absl_status.code()));
  my_status.set_message(std::string(absl_status.message()));
  my_status.add_details()->PackFrom(error_info);

  return my_status;
}

void SetErrorInfo(const intrinsic_proto::skills::SkillErrorInfo& error_info,
                  absl::Status& status) {
  status.SetPayload("type.googleapis.com/" + error_info.GetTypeName(),
                    absl::Cord(error_info.SerializeAsString()));
}

intrinsic_proto::skills::SkillErrorInfo GetErrorInfo(
    const absl::Status& status) {
  intrinsic_proto::skills::SkillErrorInfo error_info;
  std::optional<absl::Cord> error_info_cord = status.GetPayload(
      "type.googleapis.com/" +
      intrinsic_proto::skills::SkillErrorInfo::descriptor()->full_name());
  if (error_info_cord) {
    error_info.ParseFromString(std::string(error_info_cord.value()));  // NOLINT
  }
  return error_info;
}

}  // namespace skills
}  // namespace intrinsic
