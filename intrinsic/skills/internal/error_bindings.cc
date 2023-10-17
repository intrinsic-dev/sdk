// Copyright 2023 Intrinsic Innovation LLC

#include <pybind11/pybind11.h>

#include "absl/status/status.h"
#include "absl/strings/string_view.h"
#include "pybind11_abseil/status_casters.h"  // IWYU pragma: keep

namespace intrinsic {
namespace skills {

absl::Status RaiseStatus(absl::StatusCode code, absl::string_view text = "") {
  return absl::Status(code, text);
}

PYBIND11_MODULE(error_bindings, m) {
  // Immediately raise the created status as an error.
  m.def("raise_status", &RaiseStatus, "Creates a not ok status.",
        pybind11::arg("code"), pybind11::arg("text") = "");
}

}  // namespace skills
}  // namespace intrinsic
