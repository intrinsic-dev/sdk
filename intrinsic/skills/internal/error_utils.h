// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_
#define INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_

#include <string>

#include "absl/status/status.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/grpcpp.h"
#include "intrinsic/skills/proto/error.pb.h"

namespace intrinsic {
namespace skills {

// Skill service rpcs use a particular formatting of grpc::Status errors to pass
// additional metadata. The calls below help translate to and from absl::Status.
//
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

// Note, the returned absl_status will contain the SkillErrorInfo as a payload.
absl::Status ToAbslStatus(const ::grpc::Status& grpc_status);
::grpc::Status ToGrpcStatus(
    const absl::Status& absl_status,
    const intrinsic_proto::skills::SkillErrorInfo& error_info);
::grpc::Status ToGrpcStatus(const ::google::rpc::Status& rpc_status);
::google::rpc::Status ToGoogleRpcStatus(
    const absl::Status& absl_status,
    const intrinsic_proto::skills::SkillErrorInfo& error_info);

void SetErrorInfo(const intrinsic_proto::skills::SkillErrorInfo& error_info,
                  absl::Status& status);
intrinsic_proto::skills::SkillErrorInfo GetErrorInfo(
    const absl::Status& status);

// T should be a PredictionSummary, FootprintSummary, or ExecutionSummary.
template <typename T>
void AddErrorToSummary(const absl::Status& absl_status, T& summary) {
  if (absl_status.ok()) return;
  summary.set_error_code(absl_status.raw_code());
  summary.set_error_message(std::string(absl_status.message()));
  *summary.mutable_error_info() = GetErrorInfo(absl_status);
}

}  // namespace skills
}  // namespace intrinsic

#endif  // INTRINSIC_SKILLS_INTERNAL_ERROR_UTILS_H_
