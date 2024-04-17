// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/status_conversion_rpc.h"

#include <string>

#include "absl/log/log.h"
#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"
#include "google/protobuf/any.pb.h"
#include "google/rpc/status.pb.h"
#include "intrinsic/util/proto/type_url.h"

namespace intrinsic {

google::rpc::Status SaveStatusAsRpcStatus(const absl::Status& status) {
  google::rpc::Status ret;
  ret.set_code(static_cast<int>(status.code()));
  ret.set_message(status.message());
  status.ForEachPayload(
      [&](absl::string_view type_url, const absl::Cord& payload) {
        if (!type_url.starts_with(kTypeUrlPrefix)) {
          LOG(WARNING)
              << "Status payload " << type_url
              << " is not a proper type URL, not serializing into RPC status";
        } else {
          google::protobuf::Any* any = ret.add_details();
          any->set_type_url(type_url);

          any->set_value(std::string(payload));
        }
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

absl::Status MakeStatusFromRpcStatusWithPayloads(
    const google::rpc::Status& status, const absl::Status& copy_payloads_from) {
  if (status.code() == 0) return absl::OkStatus();

  absl::Status ret(static_cast<absl::StatusCode>(status.code()),
                   status.message());

  // Copy the status we base this on to the returned status
  copy_payloads_from.ForEachPayload(
      [&ret](absl::string_view type_url, const absl::Cord& payload) {
        ret.SetPayload(type_url, payload);
      });

  // Now copy the status details to payloads
  for (const google::protobuf::Any& detail : status.details()) {
    if (detail.type_url() == absl::StrCat(kTypeUrlPrefix, "util.StatusProto")) {
      // Google-specific status information that we cannot parse
      continue;
    }
    ret.SetPayload(detail.type_url(), absl::Cord(detail.value()));
  }
  return ret;
}

}  // namespace intrinsic
