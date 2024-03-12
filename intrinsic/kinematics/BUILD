# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "validate_link_parameters",
    srcs = ["validate_link_parameters.cc"],
    hdrs = ["validate_link_parameters.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/kinematics/types:to_string",
        "@com_gitlab_libeigen_eigen//:eigen",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:string_view",
    ],
)
