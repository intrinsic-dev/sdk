// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ASSETS_TESTING_ID_TEST_UTILS_H_
#define INTRINSIC_ASSETS_TESTING_ID_TEST_UTILS_H_

#include <string>

#include "absl/strings/string_view.h"

namespace intrinsic {

inline constexpr absl::string_view kTestVersion = "0.0.1";

// Constructs an ID version for the given name that is suitable for use in a
// test.
//
// The resulting string is: `ai.intrinsic.<name>.<kTestVersion>`.
//
// If all characters in the name are not in [a-zA-Z_], there is no guarantee
// that the resulting id is valid.
std::string TestIdVersionFrom(absl::string_view name);

}  // namespace intrinsic

#endif  // INTRINSIC_ASSETS_TESTING_ID_TEST_UTILS_H_
