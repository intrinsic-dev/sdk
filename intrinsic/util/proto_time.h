// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_UTIL_PROTO_TIME_H_
#define INTRINSIC_UTIL_PROTO_TIME_H_

#include "absl/status/statusor.h"
#include "absl/time/clock.h"
#include "google/protobuf/duration.pb.h"
#include "google/protobuf/timestamp.pb.h"

namespace intrinsic {

// Converts a absl::Time to its equivalent google::protobuf::Timestamp.
//
// Returns an error if the time given is invalid.
absl::Status ToProto(absl::Time time, google::protobuf::Timestamp* timestamp);
absl::StatusOr<google::protobuf::Timestamp> ToProto(absl::Time time);

// Converts an absl:Time to a google::protobuf::Timestamp, clamping to the valid
// time range allowed in `protobuf/timestamp.proto`. This allows
// absl::InfiniteFuture() and absl::InfinitePast() to be used. Note that
// roundtrip with `FromProto(ToProtoClampToValidRange(timestamp_proto))` may
// differ from `timestamp_proto`.
google::protobuf::Timestamp ToProtoClampToValidRange(absl::Time time);

// Converts a google::protobuf::Timestamp to its equivalent absl::Time.
//
// Returns an error if the timestamp given is invalid.
absl::StatusOr<absl::Time> FromProto(const google::protobuf::Timestamp& proto);

// Converts a google::protobuf::Duration to its equivalent absl::Duration.
absl::Duration FromProto(const google::protobuf::Duration& proto);

// Convenience function for setting a proto with the current time.
google::protobuf::Timestamp GetCurrentTimeProto();

// Converts a absl::Duration to its equivalent google::protobuf::Duration.
//
// Returns an error if the time given is invalid.
absl::StatusOr<google::protobuf::Duration> ToProto(absl::Duration d);
absl::Status ToProto(absl::Duration d, google::protobuf::Duration* proto);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_TIME_H_
