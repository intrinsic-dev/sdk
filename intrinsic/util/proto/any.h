// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_UTIL_PROTO_ANY_H_
#define INTRINSIC_UTIL_PROTO_ANY_H_

#include <type_traits>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/message.h"

namespace intrinsic {

// Helper to unpack an Any proto into a specific message type.  Returns
// absl::InvalidArgumentError if the message type of `any` does not match
// ParamT.
template <typename ParamT>
absl::StatusOr<ParamT> UnpackAny(const google::protobuf::Any& any) {
  static_assert(std::is_base_of<google::protobuf::Message, ParamT>::value,
                "UnpackAny() template parameter ParamT must be a "
                "google::protobuf::Message.");
  ParamT unpacked;
  if (!any.UnpackTo(&unpacked)) {
    return absl::InvalidArgumentError(absl::StrCat(
        "Unable to unpack: Incorrect message type, `any` must be of type ",
        unpacked.descriptor()->full_name(), ", but has type \"", any.type_url(),
        "\""));
  }
  return unpacked;
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_ANY_H_
