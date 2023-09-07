// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/assets/testing/id_test_utils.h"

#include <string>

#include "absl/strings/str_cat.h"

namespace intrinsic {

std::string TestIdVersionFrom(absl::string_view name) {
  return absl::StrCat("ai.intrinsic.", name, ".", kTestVersion);
}

}  // namespace intrinsic
