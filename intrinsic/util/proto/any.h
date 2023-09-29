// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_UTIL_PROTO_ANY_H_
#define INTRINSIC_UTIL_PROTO_ANY_H_

#include <optional>
#include <type_traits>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_format.h"
#include "google/protobuf/any.pb.h"
#include "google/protobuf/descriptor.h"
#include "google/protobuf/message.h"
#include "intrinsic/icon/release/status_helpers.h"
#include "intrinsic/util/proto/merge.h"

namespace intrinsic {

// Unpacks an Any proto into a specific message type.
//
// Returns absl::InvalidArgumentError if the message type of `any` does not
// match ParamT.
template <typename ParamT>
absl::StatusOr<ParamT> UnpackAny(const google::protobuf::Any& any) {
  static_assert(std::is_base_of<google::protobuf::Message, ParamT>::value,
                "UnpackAny() template parameter ParamT must be a "
                "google::protobuf::Message.");
  if (any.type_url().empty()) {
    return absl::InvalidArgumentError(absl::StrFormat(
        "Cannot unpack empty Any to %s", ParamT::descriptor()->full_name()));
  }
  if (!any.Is<ParamT>()) {
    return absl::InvalidArgumentError(
        absl::StrFormat("Cannot unpack Any of type %s to %s.", any.type_url(),
                        ParamT::descriptor()->full_name()));
  }

  ParamT unpacked;
  if (!any.UnpackTo(&unpacked)) {
    return absl::InternalError(
        absl::StrFormat("Failed to unpack Any of type %s to %s.",
                        any.type_url(), ParamT::descriptor()->full_name()));
  }

  return unpacked;
}

// Unpacks an Any proto into a specific message type, with default values
// optionally merged into unset fields.
//
// Merging does not recurse into sub-fields.
//
// Returns absl::InvalidArgumentError if the message types of `any` or
// `defaults_any` do not match ParamT.
template <typename ParamT>
absl::StatusOr<ParamT> UnpackAnyAndMerge(
    const google::protobuf::Any& any,
    const std::optional<::google::protobuf::Any>& defaults_any) {
  INTRINSIC_ASSIGN_OR_RETURN(ParamT unpacked, UnpackAny<ParamT>(any));
  if (defaults_any.has_value()) {
    INTRINSIC_ASSIGN_OR_RETURN(ParamT defaults,
                               UnpackAny<ParamT>(*defaults_any));
    INTRINSIC_RETURN_IF_ERROR(MergeUnset(defaults, unpacked));
  }

  return unpacked;
}

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_ANY_H_
