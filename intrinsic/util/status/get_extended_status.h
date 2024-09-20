// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_STATUS_GET_EXTENDED_STATUS_H_
#define INTRINSIC_UTIL_STATUS_GET_EXTENDED_STATUS_H_

#include <optional>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "google/rpc/status.pb.h"
#include "grpcpp/support/status.h"
#include "intrinsic/util/status/extended_status.pb.h"

namespace intrinsic {

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const absl::Status& status);

template <typename T>
std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const absl::StatusOr<T>& status_or) {
  return GetExtendedStatus(status_or.status());
}

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const grpc::Status& status);

std::optional<intrinsic_proto::status::ExtendedStatus> GetExtendedStatus(
    const google::rpc::Status& status);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_STATUS_GET_EXTENDED_STATUS_H_
