# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")
load("//intrinsic/platform:fbs_library.bzl", "fbs_library")

package(default_visibility = ["//visibility:public"])

fbs_library(
    name = "hardware_module_state_fbs",
    srcs = [
        "hardware_module_state.fbs",
    ],
)

cc_fbs_library(
    name = "hardware_module_state_fbs_cc",
    deps = [":hardware_module_state_fbs"],
)

cc_library(
    name = "hardware_module_state_fbs_utils",
    srcs = ["hardware_module_state_utils.cc"],
    hdrs = [
        "hardware_module_state_utils.h",
    ],
    deps = [
        ":hardware_module_state_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

fbs_library(
    name = "joint_command_fbs",
    srcs = [
        "joint_command.fbs",
    ],
)

cc_fbs_library(
    name = "joint_command_fbs_cc",
    deps = [":joint_command_fbs"],
)

cc_library(
    name = "joint_command_fbs_utils",
    srcs = ["joint_command_utils.cc"],
    hdrs = [
        "joint_command_utils.h",
    ],
    deps = [
        ":joint_command_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

fbs_library(
    name = "joint_state_fbs",
    srcs = [
        "joint_state.fbs",
    ],
)

cc_fbs_library(
    name = "joint_state_fbs_cc",
    deps = [":joint_state_fbs"],
)

cc_library(
    name = "joint_state_fbs_utils",
    srcs = ["joint_state_utils.cc"],
    hdrs = [
        "joint_state_utils.h",
    ],
    deps = [
        ":joint_state_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

fbs_library(
    name = "joint_limits_fbs",
    srcs = [
        "joint_limits.fbs",
    ],
)

cc_fbs_library(
    name = "joint_limits_fbs_cc",
    deps = [":joint_limits_fbs"],
)

cc_library(
    name = "joint_limits_fbs_utils",
    srcs = ["joint_limits_utils.cc"],
    hdrs = [
        "joint_limits_utils.h",
    ],
    deps = [
        ":joint_limits_fbs_cc",
        "//intrinsic/icon/hal:hardware_interface_handle",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/kinematics/types:joint_limits_cc_proto",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_protobuf//:protobuf_lite",
    ],
)
