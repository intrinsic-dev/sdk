// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/icon/release/status_helpers.h"

#include <string>

#include "absl/strings/str_cat.h"
#include "google/protobuf/any.pb.h"

namespace intrinsic {
google::rpc::Status SaveStatusAsRpcStatus(const absl::Status& status) {
  google::rpc::Status ret;
  ret.set_code(static_cast<int>(status.code()));
  ret.set_message(std::string(status.message()));
  status.ForEachPayload(
      [&](absl::string_view type_url, const absl::Cord& payload) {
        google::protobuf::Any* any = ret.add_details();
        any->set_type_url(std::string(type_url));
        any->set_value(std::string(payload));
      });
  return ret;
}

absl::Status MakeStatusFromRpcStatus(const google::rpc::Status& status) {
  if (status.code() == 0) return absl::OkStatus();
  absl::Status ret(static_cast<absl::StatusCode>(status.code()),
                   status.message());
  for (const google::protobuf::Any& detail : status.details()) {
    ret.SetPayload(detail.type_url(), absl::Cord(detail.value()));
  }
  return ret;
}

absl::Status AnnotateError(const absl::Status& status,
                           absl::string_view message) {
  if (status.ok()) {
    return status;
  }
  auto new_status = absl::Status(status.code(),
                                 absl::StrCat(status.message(), "; ", message));
  status.ForEachPayload(
      [&new_status](absl::string_view type_url, const absl::Cord& payload) {
        new_status.SetPayload(type_url, payload);
      });
  return new_status;
}
}  // namespace intrinsic
