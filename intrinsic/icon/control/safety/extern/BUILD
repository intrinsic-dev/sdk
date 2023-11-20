# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")

# This package provides ICON safety interfaces shared with external safety providers.
load("//intrinsic/platform:fbs_library.bzl", "fbs_library")

package(
    # No package outside of "safety" should see this.
    default_visibility = [
        "//intrinsic/icon/control/safety",
    ],
)

exports_files(
    srcs = [
        "BUILD",
        "safety_status.fbs",
    ],
    visibility = [
        "//intrinsic/production:__pkg__",
    ],
)

fbs_library(
    name = "safety_status_fbs",
    srcs = [
        "safety_status.fbs",
    ],
)

cc_fbs_library(
    name = "safety_status_fbs_cc",
    visibility = [
        # HAL arm part uses this
        "//intrinsic/icon/control:__subpackages__",
    ],
    deps = [":safety_status_fbs"],
)
