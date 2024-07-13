// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_UTIL_PROTO_TIME_H_
#define INTRINSIC_UTIL_PROTO_TIME_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/time/time.h"
#include "google/protobuf/duration.pb.h"
#include "google/protobuf/timestamp.pb.h"

namespace intrinsic {

/// google::protobuf::Timestamp.

google::protobuf::Timestamp GetCurrentTimeProto();

// Maps between a google::protobuf::Timestamp and an absl::Time.
//
// Returns an error if either end of the mapping involves a timestamp that is
// outside the range allowed in `google/protobuf/timestamp.proto`.
absl::Status FromAbslTime(absl::Time time,
                          google::protobuf::Timestamp* timestamp);
absl::StatusOr<google::protobuf::Timestamp> FromAbslTime(absl::Time time);
absl::StatusOr<absl::Time> ToAbslTime(const google::protobuf::Timestamp& proto);

// Converts an absl:Time to a google::protobuf::Timestamp, clamping to the valid
// time range allowed in `google/protobuf/timestamp.proto`.
//
// This allows absl::InfiniteFuture() and absl::InfinitePast() to be used.
//
// Note that roundtrip with
// `ToAbslTime(FromAbslTimeClampToValidRange(timestamp_proto))` may differ from
// `timestamp_proto`.
google::protobuf::Timestamp FromAbslTimeClampToValidRange(absl::Time time);

// Converts a floating-point time quantity since the Unix epoch to
// google::protobuf::Timestamp.
//
// A google::protobuf::Timestamp is defined in `google/protobuf/timestamp.proto`
// as a time quantity since Unix epoch, so this conversion makes sense.
//
// Returns an error if the input value would result in a timestamp that is
// outside the range allowed in `google/protobuf/timestamp.proto`.
absl::Status FromUnixDoubleNanos(double ns,
                                 google::protobuf::Timestamp* timestamp);
absl::Status FromUnixDoubleMicros(double us,
                                  google::protobuf::Timestamp* timestamp);
absl::Status FromUnixDoubleMillis(double ms,
                                  google::protobuf::Timestamp* timestamp);
absl::Status FromUnixDoubleSeconds(double s,
                                   google::protobuf::Timestamp* timestamp);
absl::StatusOr<google::protobuf::Timestamp> FromUnixDoubleNanos(double ns);
absl::StatusOr<google::protobuf::Timestamp> FromUnixDoubleMicros(double us);
absl::StatusOr<google::protobuf::Timestamp> FromUnixDoubleMillis(double ms);
absl::StatusOr<google::protobuf::Timestamp> FromUnixDoubleSeconds(double s);

// Converts a google::protobuf::Timestamp to a floating-point time quantity
// since the Unix epoch.
//
// NOTE: Precision loss may occur for large values.
//
// A google::protobuf::Timestamp is defined in `google/protobuf/timestamp.proto`
// as a time quantity since Unix epoch, so this conversion makes sense.
//
// Returns an error if the input timestamp has a value that is outside the range
// allowed in `google/protobuf/timestamp.proto`.
absl::StatusOr<double> ToUnixDoubleNanos(
    const google::protobuf::Timestamp& proto);
absl::StatusOr<double> ToUnixDoubleMicros(
    const google::protobuf::Timestamp& proto);
absl::StatusOr<double> ToUnixDoubleMillis(
    const google::protobuf::Timestamp& proto);
absl::StatusOr<double> ToUnixDoubleSeconds(
    const google::protobuf::Timestamp& proto);

/// google::protobuf::Duration.

// Maps between a google::protobuf::Duration and an absl::Duration.
//
// Returns an error if either end of the mapping involves a duration that is
// outside the range allowed in `google/protobuf/duration.proto`.
absl::StatusOr<google::protobuf::Duration> FromAbslDuration(absl::Duration d);
absl::Status FromAbslDuration(absl::Duration d,
                              google::protobuf::Duration* proto);
absl::Duration ToAbslDuration(const google::protobuf::Duration& proto);

}  // namespace intrinsic

#endif  // INTRINSIC_UTIL_PROTO_TIME_H_
