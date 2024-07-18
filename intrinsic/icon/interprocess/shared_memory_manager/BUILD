# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:flatbuffers.bzl", "cc_flatbuffers_library", "flatbuffers_library")

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

flatbuffers_library(
    name = "segment_info_fbs",
    srcs = ["segment_info.fbs"],
)

cc_flatbuffers_library(
    name = "segment_info_fbs_cc",
    deps = ["segment_info_fbs"],
)

cc_library(
    name = "segment_info_utils",
    srcs = ["segment_info_utils.cc"],
    hdrs = ["segment_info_utils.h"],
    deps = [":segment_info_fbs_cc"],
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
    # but won't complain if specified explicitly here.
    linkopts = [
        "-lrt",
    ],
    deps = [
        ":memory_segment",
        ":segment_header",
        ":segment_info_fbs_cc",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
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
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)
