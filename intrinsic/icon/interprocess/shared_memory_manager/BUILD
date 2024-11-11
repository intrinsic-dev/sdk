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
    srcs = ["shared_memory_manager.cc"],
    hdrs = ["shared_memory_manager.h"],
    # With gcc we explicitly have to link against librt,
    # providing POSIX functions for shared memory, such as shm_open.
    # Clang automatically links against it,
    # but won't complain if specified explicitly here.
    linkopts = [
        "-lrt",
    ],
    deps = [
        ":domain_socket_utils",
        ":memory_segment",
        ":segment_header",
        ":segment_info_fbs_cc",
        "//intrinsic/icon/flatbuffers:flatbuffer_utils",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)

cc_library(
    name = "memory_segment",
    srcs = ["memory_segment.cc"],
    hdrs = ["memory_segment.h"],
    deps = [
        ":domain_socket_utils",
        ":segment_header",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "domain_socket_server",
    srcs = ["domain_socket_server.cc"],
    hdrs = ["domain_socket_server.h"],
    deps = [
        ":domain_socket_utils",
        ":segment_info_fbs_cc",
        ":shared_memory_manager",
        "//intrinsic/icon/hal:hardware_interface_registry",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread",
        "//intrinsic/util/thread:thread_options",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
        "@or_tools//ortools/base:file",
        "@or_tools//ortools/base:path",
    ],
)

cc_library(
    name = "domain_socket_utils",
    srcs = ["domain_socket_utils.cc"],
    hdrs = ["domain_socket_utils.h"],
    deps = [
        ":segment_info_fbs_cc",
        ":segment_info_utils",
        "//intrinsic/icon/flatbuffers:flatbuffer_utils",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/time",
        "@or_tools//ortools/base:file",
        "@or_tools//ortools/base:path",
    ],
)
