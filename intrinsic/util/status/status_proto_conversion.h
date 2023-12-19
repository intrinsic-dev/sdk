// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_STATUS_PROTO_CONVERSION_H_
#define INTRINSIC_UTIL_STATUS_STATUS_PROTO_CONVERSION_H_

#include "absl/status/status.h"
#include "intrinsic/util/status/status.pb.h"

namespace intrinsic {

// Convert an absl::Status to a Intrinsic-specific StatusProto. The proto will
// contain the code. If the code is not Ok then it will also contain the message
// and any additional payloads that the input Status may have.
//
// The out parameter must not be a nullptr.
void SaveStatusToProto(const absl::Status& status,
                       intrinsic_proto::StatusProto* out);

// Convert a StatusProto to an absl::Status. This takes the code and message as
// well as payloads and creates a new absl::Status with that information.
absl::Status MakeStatusFromProto(const intrinsic_proto::StatusProto& proto);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_STATUS_PROTO_CONVERSION_H_
