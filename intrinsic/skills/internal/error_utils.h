// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_
#define INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_

#include <optional>
#include <string>
#include <utility>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "google/rpc/status.pb.h"
#include "intrinsic/logging/proto/context.pb.h"
#include "intrinsic/skills/internal/runtime_data.h"
#include "intrinsic/skills/proto/error.pb.h"
#include "intrinsic/util/status/extended_status.pb.h"
#include "intrinsic/util/status/get_extended_status.h"

namespace intrinsic {
namespace skills {

// Details
//
// There is some differences in error handling between c++ and python grpc
// servers and the following approach was chosen in order to minimize the
// differences when client interacts with the servers.
//
// The c++ grpc api returns a grpc::Status object on the client side and on the
// server side. The sending is straight forward, as the client will see that
// same Status that is returned by the server. This Status object contains a
// code, a human readable message, and an arbitrary "details" string used to
// contain additional data.
//
// The python grpc api returns a code and message, but additional data is sent
// through a side channel called "trailing metadata". However, when a special
// key is present in this metadata, a c++ grpc client (and hopefully other
// clients) will use that side channel information to populate the contents of
// the details field of the Status obtained by the c++ grpc client. The catch is
// that the python server always populates the metadata with a serialized
// google.rpc.Status proto.
//
// Thus, we make the choice of returning a serialized google.rpc.Status proto
// in the details field of the grpc.Status in both the c++ and python servers.

intrinsic_proto::skills::SkillErrorInfo GetErrorInfo(
    const absl::Status& status);

// Creates a skill error augmenting the given status.
// This will augment and extended status attached as payload in the following
// ways:
// - if component not set, sets skill id
// - if component set that doesn't match skill ID wraps ES
// - if timestamp not set, sets it to "now"
// - if log_context provided and non set already set it
// If no extended status is found, will convert the legacy status.
::google::rpc::Status CreateSkillError(
    absl::Status status, absl::string_view skill_id, absl::string_view op_name,
    const internal::StatusSpecs& status_specs,
    std::optional<intrinsic_proto::data_logger::Context> log_context);

// T should be a PredictionSummary, FootprintSummary, or ExecutionSummary.
template <typename T>
void AddErrorToSummary(const absl::Status& absl_status, T& summary) {
  if (absl_status.ok()) return;
  std::optional<intrinsic_proto::status::ExtendedStatus> extended_status =
      GetExtendedStatus(absl_status);

  if (extended_status.has_value()) {
    *summary.mutable_extended_status() = std::move(*extended_status);
  } else {
    summary.set_error_code(absl_status.raw_code());
    summary.set_error_message(std::string(absl_status.message()));
  }
  *summary.mutable_error_info() = GetErrorInfo(absl_status);
}

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_
