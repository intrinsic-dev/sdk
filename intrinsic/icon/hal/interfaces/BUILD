# Copyright 2023 Intrinsic Innovation LLC

load("//intrinsic/platform:flatbuffers.bzl", "cc_flatbuffers_library", "flatbuffers_library")

package(default_visibility = ["//visibility:public"])

flatbuffers_library(
    name = "control_mode_fbs",
    srcs = [
        "control_mode.fbs",
    ],
)

cc_flatbuffers_library(
    name = "control_mode_fbs_cc",
    deps = [":control_mode_fbs"],
)

cc_library(
    name = "control_mode_fbs_utils",
    srcs = [
        "control_mode_utils.cc",
    ],
    hdrs = [
        "control_mode_utils.h",
    ],
    deps = [
        ":control_mode_fbs_cc",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

flatbuffers_library(
    name = "hardware_module_state_fbs",
    srcs = [
        "hardware_module_state.fbs",
    ],
)

cc_flatbuffers_library(
    name = "hardware_module_state_fbs_cc",
    deps = [
        ":hardware_module_state_fbs",
    ],
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

flatbuffers_library(
    name = "icon_state_fbs",
    srcs = [
        "icon_state.fbs",
    ],
)

cc_flatbuffers_library(
    name = "icon_state_fbs_cc",
    deps = [":icon_state_fbs"],
)

cc_library(
    name = "icon_state_fbs_utils",
    srcs = ["icon_state_utils.cc"],
    hdrs = [
        "icon_state_utils.h",
    ],
    deps = [
        ":icon_state_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

flatbuffers_library(
    name = "imu_fbs",
    srcs = [
        "imu.fbs",
    ],
    deps = [
        "//intrinsic/icon/flatbuffers:transform_types_fbs",
    ],
)

cc_flatbuffers_library(
    name = "imu_fbs_cc",
    deps = [":imu_fbs"],
)

cc_library(
    name = "imu_fbs_utils",
    srcs = [
        "imu_utils.cc",
    ],
    hdrs = [
        "imu_utils.h",
    ],
    deps = [
        ":imu_fbs_cc",
        "//intrinsic/icon/flatbuffers:transform_types_fbs_cc",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

flatbuffers_library(
    name = "joint_command_fbs",
    srcs = [
        "joint_command.fbs",
    ],
)

cc_flatbuffers_library(
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
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

flatbuffers_library(
    name = "joint_limits_fbs",
    srcs = [
        "joint_limits.fbs",
    ],
)

cc_flatbuffers_library(
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
        "//intrinsic/kinematics/types:joint_limits_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)

flatbuffers_library(
    name = "joint_state_fbs",
    srcs = [
        "joint_state.fbs",
    ],
)

cc_flatbuffers_library(
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

flatbuffers_library(
    name = "robot_controller_fbs",
    srcs = [
        "robot_controller.fbs",
    ],
)

cc_flatbuffers_library(
    name = "robot_controller_fbs_cc",
    deps = [":robot_controller_fbs"],
)

cc_library(
    name = "robot_controller_fbs_utils",
    srcs = ["robot_controller_utils.cc"],
    hdrs = [
        "robot_controller_utils.h",
    ],
    deps = [
        ":robot_controller_fbs_cc",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)
