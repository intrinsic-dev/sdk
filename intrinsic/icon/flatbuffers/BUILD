# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:flatbuffers.bzl", "cc_flatbuffers_library", "flatbuffers_library")

package(default_visibility = ["//visibility:public"])

flatbuffers_library(
    name = "transform_types_fbs",
    srcs = ["transform_types.fbs"],
)

cc_flatbuffers_library(
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
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_gitlab_libeigen_eigen//:eigen",
    ],
)

cc_library(
    name = "flatbuffer_utils",
    hdrs = ["flatbuffer_utils.h"],
    deps = ["@com_github_google_flatbuffers//:runtime_cc"],
)

cc_test(
    name = "flatbuffer_utils_test",
    srcs = ["flatbuffer_utils_test.cc"],
    deps = [
        ":flatbuffer_utils",
        "//intrinsic/icon/interprocess/shared_memory_manager:segment_info_fbs_cc",
        "//intrinsic/util/testing:gtest_wrapper",
    ],
)
