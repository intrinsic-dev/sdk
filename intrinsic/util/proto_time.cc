// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/proto_time.h"

#include <algorithm>
#include <cstdint>
#include <ctime>

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/strings/str_cat.h"
#include "absl/time/clock.h"
#include "absl/time/time.h"

namespace intrinsic {

namespace {

// Minimum valid value for google::protobuf::Timestamp nanos().
constexpr int kMinProtoTimestampNanos = 0;
// Maximum valid value for google::protobuf::Timestamp nanos().
constexpr int kMaxProtoTimestampNanos = 999999999;
// Earliest time that can be represented by a google::protobuf::Timestamp.
// Corresponds to 0001-01-01T00:00:00Z. See google/protobuf/timestamp.proto.
constexpr timespec kMinProtoTimestamp{.tv_sec = -62135596800,
                                      .tv_nsec = kMinProtoTimestampNanos};
// Latest time that can be represented by a google::protobuf::Timestamp.
// Corresponds to 9999-12-31T23:59:59.999999999Z. See
// google/protobuf/timestamp.proto.
constexpr timespec kMaxProtoTimestamp{.tv_sec = 253402300799,
                                      .tv_nsec = kMaxProtoTimestampNanos};

// Validation requirements documented in duration.proto
absl::Status Validate(const google::protobuf::Duration& d) {
  const auto sec = d.seconds();
  const auto ns = d.nanos();
  if (sec < -315576000000 || sec > 315576000000) {
    return absl::InvalidArgumentError(absl::StrCat("seconds=", sec));
  }
  if (ns < -999999999 || ns > 999999999) {
    return absl::InvalidArgumentError(absl::StrCat("nanos=", ns));
  }
  if ((sec < 0 && ns > 0) || (sec > 0 && ns < 0)) {
    return absl::InvalidArgumentError("sign mismatch");
  }
  return absl::OkStatus();
}

// Documented in google/protobuf/timestamp.proto.
absl::Status Validate(const google::protobuf::Timestamp& timestamp) {
  const auto sec = timestamp.seconds();
  const auto ns = timestamp.nanos();
  absl::Status status = absl::OkStatus();
  // sec must be [0001-01-01T00:00:00Z, 9999-12-31T23:59:59.999999999Z]
  if (sec < kMinProtoTimestamp.tv_sec || sec > kMaxProtoTimestamp.tv_sec) {
    status = absl::InvalidArgumentError(absl::StrCat("seconds=", sec));
  } else if (ns < kMinProtoTimestampNanos || ns > kMaxProtoTimestampNanos) {
    status = absl::InvalidArgumentError(absl::StrCat("nanos=", ns));
  }
  return status;
}

void ToProtoNoValidation(absl::Time time,
                         google::protobuf::Timestamp* timestamp) {
  const int64_t s = absl::ToUnixSeconds(time);
  timestamp->set_seconds(s);
  timestamp->set_nanos((time - absl::FromUnixSeconds(s)) /
                       absl::Nanoseconds(1));
}

}  // namespace

absl::Status ToProto(absl::Time time, google::protobuf::Timestamp* timestamp) {
  ToProtoNoValidation(time, timestamp);
  return Validate(*timestamp);
}

absl::StatusOr<google::protobuf::Timestamp> ToProto(absl::Time time) {
  google::protobuf::Timestamp timestamp;
  auto status = ToProto(time, &timestamp);
  if (!status.ok()) {
    return status;
  }
  return timestamp;
}

google::protobuf::Timestamp ToProtoClampToValidRange(absl::Time time) {
  time = std::clamp(time, absl::TimeFromTimespec(kMinProtoTimestamp),
                    absl::TimeFromTimespec(kMaxProtoTimestamp));
  google::protobuf::Timestamp out;
  ToProtoNoValidation(time, &out);
  return out;
}

absl::StatusOr<absl::Time> FromProto(const google::protobuf::Timestamp& proto) {
  absl::Status status = Validate(proto);
  if (!status.ok()) return status;
  return absl::FromUnixSeconds(proto.seconds()) +
         absl::Nanoseconds(proto.nanos());
}

absl::Duration FromProto(const google::protobuf::Duration& proto) {
  return absl::Seconds(proto.seconds()) + absl::Nanoseconds(proto.nanos());
}

google::protobuf::Timestamp GetCurrentTimeProto() {
  auto time_or = ToProto(absl::Now());
  if (!time_or.ok()) {
    return google::protobuf::Timestamp();
  }
  return *time_or;
}

absl::StatusOr<google::protobuf::Duration> ToProto(absl::Duration d) {
  google::protobuf::Duration proto;
  absl::Status status = ToProto(d, &proto);
  if (!status.ok()) return status;
  return proto;
}

absl::Status ToProto(absl::Duration d, google::protobuf::Duration* proto) {
  // s and n may both be negative, per the Duration proto spec.
  const int64_t s = absl::IDivDuration(d, absl::Seconds(1), &d);
  const int64_t n = absl::IDivDuration(d, absl::Nanoseconds(1), &d);
  proto->set_seconds(s);
  proto->set_nanos(n);
  return Validate(*proto);
}

}  // namespace intrinsic
