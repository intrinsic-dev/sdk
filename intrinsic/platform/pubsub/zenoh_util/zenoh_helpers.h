// Copyright 2023 Intrinsic Innovation LLC

#ifndef INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HELPERS_H_
#define INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HELPERS_H_

#include "absl/status/status.h"
#include "absl/strings/string_view.h"

namespace intrinsic {

bool RunningUnderTest();

bool RunningInKubernetes();

// Returns true if the given keyexpr is follows the zenoh keyexpr format
// listed at https://zenoh.io/docs/manual/abstractions/.
//
// In short a keyexpr is a string of UTF-8 characters joined by `/`.
// *, $, ?, # are not allowed. *, $*, and ** carry special meaning.
//
// * can be used in between two namespaces like /a/*/b to match all keys
// starting with /a/ and ending with /b.
//
// $* can be used to within a namespace like /a/b$*/c to match all keys
// starting with a/b and ending with /c.
//
// ** can be used to match all keys like a/**/d matches all keys starting with
// a/ and ending with /c including /a/b/c/d or a/b/e/d.
absl::Status ValidZenohKeyexpr(absl::string_view);

// Returns true if the given key is follows the zenoh key format
// listed at https://zenoh.io/docs/manual/abstractions/.
//
// In short a key is a string of UTF-8 characters joined by `/` and
// excluding *, $, ?, #.
absl::Status ValidZenohKey(absl::string_view);

}  // namespace intrinsic

#endif  // INTRINSIC_PLATFORM_PUBSUB_ZENOH_UTIL_ZENOH_HELPERS_H_
