# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")
load("//intrinsic/platform:fbs_library.bzl", "fbs_library")

package(default_visibility = ["//visibility:public"])

fbs_library(
    name = "transform_types_fbs",
    srcs = ["transform_types.fbs"],
)

cc_fbs_library(
    name = "transform_types_fbs_cc",
    deps = [":transform_types_fbs"],
)

cc_library(
    name = "transform_types",
    srcs = [
        "transform_types.cc",
    ],
    hdrs = [
        "transform_types.h",
    ],
    deps = [
        ":transform_types_fbs_cc",
        "//intrinsic/eigenmath",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@eigen",
    ],
)
