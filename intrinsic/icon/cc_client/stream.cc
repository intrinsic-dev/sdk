// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/cc_client/stream.h"

#include <string>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "grpcpp/support/sync_stream.h"
#include "intrinsic/icon/common/id_types.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/util/status/status_conversion_grpc.h"
#include "intrinsic/util/status/status_conversion_rpc.h"
#include "intrinsic/util/status/status_macros.h"

namespace intrinsic::icon::internal {

GenericStreamWriter::~GenericStreamWriter() {
  if (absl::Status status = FinishIfNeeded(); !status.ok()) {
    LOG(ERROR) << "Stream closing with status: " << status;
  }
}

absl::Status GenericStreamWriter::OpenStreamWriter(
    SessionId session_id, ActionInstanceId action_instance_id,
    absl::string_view input_name) {
  constexpr absl::string_view kAbortedErrorMessage =
      "Communication with server failed.";
  intrinsic_proto::icon::OpenWriteStreamRequest initial_req;
  initial_req.set_session_id(session_id.value());
  initial_req.mutable_add_write_stream()->set_action_id(
      action_instance_id.value());

  initial_req.mutable_add_write_stream()->set_field_name(

      std::string(input_name));
  if (!grpc_stream_->Write(initial_req)) {
    INTR_RETURN_IF_ERROR(FinishIfNeeded());
    return absl::AbortedError(kAbortedErrorMessage);
  }

  intrinsic_proto::icon::OpenWriteStreamResponse initial_resp;
  if (!grpc_stream_->Read(&initial_resp)) {
    INTR_RETURN_IF_ERROR(FinishIfNeeded());
    return absl::UnknownError(kAbortedErrorMessage);
  }

  if (initial_resp.stream_operation_response_case() !=
      intrinsic_proto::icon::OpenWriteStreamResponse::kAddStreamResponse) {
    return absl::UnknownError(
        "Received unexpected response from stream stream.");
  }

  INTR_RETURN_IF_ERROR(intrinsic::MakeStatusFromRpcStatus(
      initial_resp.add_stream_response().status()));

  return absl::OkStatus();
}

absl::Status GenericStreamWriter::WriteToStream(
    const google::protobuf::Message& value) {
  intrinsic_proto::icon::OpenWriteStreamRequest req;
  req.mutable_write_value()->mutable_value()->PackFrom(value);

  if (!grpc_stream_->Write(req)) {
    INTR_RETURN_IF_ERROR(FinishIfNeeded());
    return absl::AbortedError("Failed to write to stream.");
  }

  intrinsic_proto::icon::OpenWriteStreamResponse resp;
  if (!grpc_stream_->Read(&resp)) {
    INTR_RETURN_IF_ERROR(FinishIfNeeded());
    return absl::AbortedError("Failed to write to stream.");
  }

  if (!resp.has_write_value_response()) {
    INTR_RETURN_IF_ERROR(FinishIfNeeded());
    return absl::InternalError(
        "Stream write response is missing `write_value_response` field after "
        "writing a value.");
  }

  return intrinsic::MakeStatusFromRpcStatus(resp.write_value_response());
}

absl::Status GenericStreamWriter::FinishIfNeeded() {
  if (finish_status_.has_value()) {
    return *finish_status_;
  }
  // WritesDone must be called only once.
  if (!grpc_stream_->WritesDone()) {
    intrinsic_proto::icon::OpenWriteStreamResponse resp;
    while (grpc_stream_->Read(&resp)) {
      LOG(ERROR) << "Received unexpected response from the server:" << resp;
    }
  }
  finish_status_ = ToAbslStatus(grpc_stream_->Finish());
  return *finish_status_;
}

}  // namespace intrinsic::icon::internal
