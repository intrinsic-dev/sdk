# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:flatbuffers.bzl", "cc_flatbuffers_library", "flatbuffers_library")

package(default_visibility = [
    "//visibility:public",
])

exports_files(
    srcs = [
        "BUILD",
        "safety_status.fbs",
    ],
    visibility = [
        "//intrinsic/production:__pkg__",
    ],
)

flatbuffers_library(
    name = "safety_status_fbs",
    srcs = [
        "safety_status.fbs",
    ],
)

cc_flatbuffers_library(
    name = "safety_status_fbs_cc",
    deps = [":safety_status_fbs"],
)
