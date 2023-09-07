# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//intrinsic/platform:fbs_library.bzl", "fbs_library")
load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "segment_header",
    srcs = [
        "segment_header.cc",
    ],
    hdrs = [
        "segment_header.h",
    ],
    deps = [
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:log",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/strings",
    ],
)

fbs_library(
    name = "segment_info_fbs",
    srcs = ["segment_info.fbs"],
)

cc_fbs_library(
    name = "segment_info_fbs_cc",
    deps = ["segment_info_fbs"],
)

cc_library(
    name = "segment_info_utils",
    srcs = ["segment_info_utils.cc"],
    hdrs = ["segment_info_utils.h"],
    deps = [
        ":segment_info_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

cc_library(
    name = "shared_memory_manager",
    srcs = [
        "shared_memory_manager.cc",
    ],
    hdrs = [
        "shared_memory_manager.h",
    ],
    # With gcc we explicitly have to link against librt,
    # providing POSIX functions for shared memory, such as shm_open.
    # Clang automatically links against it,
    # but won't complain if specified explicilty here.
    linkopts = [
        "-lrt",
    ],
    deps = [
        ":segment_header",
        ":segment_info_fbs_cc",
        "//intrinsic/icon/release:status_helpers",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "memory_segment",
    srcs = [
        "memory_segment.cc",
    ],
    hdrs = [
        "memory_segment.h",
    ],
    deps = [
        ":segment_header",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:core_time",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)
