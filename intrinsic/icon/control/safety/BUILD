# Copyright 2023 Intrinsic Innovation LLC

# This package provides ICON safety interfaces.
load("//intrinsic/platform:fbs_library.bzl", "fbs_library")
load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")

package(default_visibility = ["//visibility:public"])

exports_files(
    srcs = [
        "BUILD",
        "safety_messages.fbs",
        "safety_messages_utils.cc",
        "safety_messages_utils.h",
    ],
    visibility = [
        "//intrinsic/production:__pkg__",
    ],
)

package_group(
    name = "icon",
    packages = [
        "//intrinsic/icon/...",
    ],
)

package_group(
    name = "safety",
    packages = [
        "//intrinsic/icon/control/safety/...",
    ],
)

fbs_library(
    name = "safety_messages_fbs",
    srcs = [
        "safety_messages.fbs",
    ],
    deps = [
        "//intrinsic/icon/control/safety/extern:safety_status_fbs",
    ],
)

cc_fbs_library(
    name = "safety_messages_fbs_cc",
    deps = [":safety_messages_fbs"],
)

cc_library(
    name = "safety_messages_fbs_utils",
    srcs = ["safety_messages_utils.cc"],
    hdrs = ["safety_messages_utils.h"],
    deps = [
        ":safety_messages_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/strings",
    ],
)
