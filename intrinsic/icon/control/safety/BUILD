# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:flatbuffers.bzl", "cc_flatbuffers_library", "flatbuffers_library")

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

flatbuffers_library(
    name = "safety_messages_fbs",
    srcs = [
        "safety_messages.fbs",
    ],
    deps = [
        "//intrinsic/icon/control/safety/extern:safety_status_fbs",
    ],
)

cc_flatbuffers_library(
    name = "safety_messages_fbs_cc",
    deps = [":safety_messages_fbs"],
)

cc_library(
    name = "safety_messages_fbs_utils",
    srcs = ["safety_messages_utils.cc"],
    hdrs = ["safety_messages_utils.h"],
    deps = [
        ":safety_messages_fbs_cc",
        "//intrinsic/icon/control/safety/extern:safety_status_fbs_cc",
        "@com_google_absl//absl/strings",
    ],
)
