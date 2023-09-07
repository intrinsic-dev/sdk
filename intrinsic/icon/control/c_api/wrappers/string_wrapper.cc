// Copyright 2023 Intrinsic Innovation LLC
// Intrinsic Proprietary and Confidential
// Provided subject to written agreement between the parties.

#include "intrinsic/icon/control/c_api/wrappers/string_wrapper.h"

#include <cstring>
#include <string>

#include "absl/strings/string_view.h"

namespace intrinsic::icon {

void DestroyString(XfaIconString* str) {
  if (str == nullptr) {
    return;
  }
  delete[] str->data;
  delete str;
}

XfaIconString* Wrap(absl::string_view str) {
  char* data = new char[str.size()];
  std::memcpy(data, str.data(), str.size());
  return new XfaIconString({.data = data, .size = str.size()});
}

const XfaIconStringView WrapView(absl::string_view str) {
  return {.data = str.data(), .size = str.size()};
}

}  // namespace intrinsic::icon
