// Copyright 2023 Intrinsic Innovation LLC

#include "intrinsic/util/status/annotate.h"

#include <string_view>

#include "absl/status/status.h"
#include "absl/strings/cord.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/string_view.h"

namespace intrinsic {

absl::Status AnnotateError(const absl::Status& status,
                           std::string_view message) {
  if (status.ok()) {
    return status;
  }
  absl::Status new_status(status.code(),
                          absl::StrCat(status.message(), "; ", message));
  status.ForEachPayload(
      [&new_status](absl::string_view type_url, const absl::Cord& payload) {
        new_status.SetPayload(type_url, payload);
      });

  return new_status;
}

}  // namespace intrinsic
