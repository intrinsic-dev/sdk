// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/cc_client/client_utils.h"

#include <string>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "intrinsic/icon/cc_client/client.h"
#include "intrinsic/icon/cc_client/condition.h"
#include "intrinsic/icon/common/builtins.h"
#include "intrinsic/icon/common/part_properties.h"

namespace intrinsic {
namespace icon {

Comparison IsDone() { return IsTrue(kIsDone); }

absl::Status SetPartProperty(const Client& client, absl::string_view part_name,
                             absl::string_view property_name,
                             double double_value) {
  return client.SetPartProperties(PartPropertyMap{
      .properties = {{std::string(part_name),
                      {{std::string(property_name), double_value}}}}});
}

absl::Status SetPartProperty(const Client& client, absl::string_view part_name,
                             absl::string_view property_name, bool bool_value) {
  return client.SetPartProperties(PartPropertyMap{
      .properties = {{std::string(part_name),
                      {{std::string(property_name), bool_value}}}}});
}

}  // namespace icon
}  // namespace intrinsic
