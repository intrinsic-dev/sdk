// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#ifndef INTRINSIC_ICON_CONTROL_C_API_WRAPPERS_STRING_WRAPPER_H_
#define INTRINSIC_ICON_CONTROL_C_API_WRAPPERS_STRING_WRAPPER_H_

#include <string>

#include "absl/strings/string_view.h"
#include "intrinsic/icon/control/c_api/c_types.h"

namespace intrinsic::icon {

// Destroys `str`, freeing both the memory for the XfaIconString struct itself
// *and* the memory for its character buffer.
void DestroyString(XfaIconString* str);

// Creates a new XfaIconString on the heap, including a buffer to move the
// contents of `str` into. The result can be passed to API functions for them to
// keep (and eventually destroy using DestroyString() above).
XfaIconString* Wrap(absl::string_view str);

// Wraps a string_view into an XfaIconString that can be passed to API functions
// as an immutable, non-owned parameter.
const XfaIconStringView WrapView(absl::string_view str);

}  // namespace intrinsic::icon

#endif  // INTRINSIC_ICON_CONTROL_C_API_WRAPPERS_STRING_WRAPPER_H_
