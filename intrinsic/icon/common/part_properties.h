// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_ICON_COMMON_PART_PROPERTIES_H_
#define INTRINSIC_ICON_COMMON_PART_PROPERTIES_H_

#include <cstddef>
#include <string>
#include <variant>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "absl/time/time.h"
#include "intrinsic/icon/proto/service.pb.h"
#include "intrinsic/third_party/intops/strong_int.h"

namespace intrinsic::icon {

// Identifier for a Part Property.
DEFINE_STRONG_INT_TYPE(PartPropertyId, size_t);

// A PartPropertyValue is the in-memory representation of a part property. It is
// stored in the AsyncBuffers that move information about part properties
// between the realtime and non-realtime thread.
// NOTE: We initialize this to one of the supported types at startup time, and
// after that point it should never change types!
using PartPropertyValue = std::variant<bool, double>;

struct TimestampedPartProperties {
  absl::Duration timestamp_control;
  absl::Time timestamp_wall;
  absl::flat_hash_map<std::string,
                      absl::flat_hash_map<std::string, PartPropertyValue>>
      properties;
};

struct PartPropertyMap {
  absl::flat_hash_map<std::string,
                      absl::flat_hash_map<std::string, PartPropertyValue>>
      properties;
};

::intrinsic_proto::icon::PartPropertyValue ToProto(
    const PartPropertyValue& value);

absl::StatusOr<PartPropertyValue> FromProto(
    const ::intrinsic_proto::icon::PartPropertyValue& value);

// Visitor to assign one PropertyValue (variant<double, bool>) to another
// without changing the type of the held value. Returns an error if `dst` holds
// a different type than `src`.
struct AssignPropertyValue {
  // These two implement the happy case and return OkStatus.
  absl::Status operator()(bool src, bool& dst);
  absl::Status operator()(double src, double& dst);
  // These two implement the error case and return InvalidArgumentError.
  absl::Status operator()(double src, bool& dst);
  absl::Status operator()(bool src, double& dst);

  // This is used for the error message in case src has a different type than
  // dst.
  std::string property_name;
};

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_COMMON_PART_PROPERTIES_H_
