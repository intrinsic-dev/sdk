// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/assets/testing/id_test_utils.h"

#include <string>

#include "absl/strings/str_cat.h"

namespace intrinsic {

std::string TestIdVersionFrom(absl::string_view name) {
  return absl::StrCat("ai.intrinsic.", name, ".", kTestVersion);
}

}  // namespace intrinsic
