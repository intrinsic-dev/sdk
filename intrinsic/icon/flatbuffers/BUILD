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

flatbuffers_library(
    name = "matrix_types_fbs",
    srcs = ["matrix_types.fbs"],
)

cc_flatbuffers_library(
    name = "matrix_types_fbs_cc",
    deps = [":matrix_types_fbs"],
)

cc_library(
    name = "matrix_types_utils",
    srcs = ["matrix_types_utils.cc"],
    hdrs = ["matrix_types_utils.h"],
    deps = [
        ":matrix_types_fbs_cc",
        "//intrinsic/eigenmath",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
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
    name = "control_types_utils",
    srcs = [
        "control_types_copy.cc",
        "control_types_view.cc",
    ],
    hdrs = [
        "control_types_copy.h",
        "control_types_view.h",
    ],
    deps = [
        ":transform_types",
        ":transform_types_fbs_cc",
        ":transform_utils",
        "//intrinsic/eigenmath",
        "//intrinsic/math:pose3",
        "//intrinsic/math:twist",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

cc_library(
    name = "transform_utils",
    srcs = [
        "transform_copy.cc",
        "transform_view.cc",
    ],
    hdrs = [
        "transform_copy.h",
        "transform_view.h",
    ],
    deps = [
        ":transform_types",
        ":transform_types_fbs_cc",
        "//intrinsic/eigenmath",
        "@com_github_google_flatbuffers//:runtime_cc",
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
