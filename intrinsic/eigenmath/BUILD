# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "eigenmath",
    hdrs = [
        "types.h",
    ],
    deps = ["@eigen"],
)

cc_library(
    name = "rotation_utils",
    hdrs = ["rotation_utils.h"],
    deps = [
        ":eigenmath",
        "@com_google_absl//absl/log:check",
        "@eigen",
    ],
)

cc_library(
    name = "so3",
    hdrs = ["so3.h"],
    deps = [
        ":eigenmath",
        ":rotation_utils",
        "@com_google_absl//absl/log:check",
        "@eigen",
    ],
)
