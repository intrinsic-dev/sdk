# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "eigenmath",
    hdrs = [
        "types.h",
    ],
    deps = ["@com_gitlab_libeigen_eigen//:eigen"],
)

cc_library(
    name = "rotation_utils",
    hdrs = ["rotation_utils.h"],
    deps = [
        ":eigenmath",
        "@com_gitlab_libeigen_eigen//:eigen",
        "@com_google_absl//absl/log:check",
    ],
)

cc_library(
    name = "so3",
    hdrs = ["so3.h"],
    deps = [
        ":eigenmath",
        ":rotation_utils",
        "@com_gitlab_libeigen_eigen//:eigen",
        "@com_google_absl//absl/log:check",
    ],
)
