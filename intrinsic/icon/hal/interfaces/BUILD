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
        "//intrinsic/icon/utils:fixed_str_cat",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_limits_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/types:span",
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

flatbuffers_library(
    name = "robot_payload_fbs",
    srcs = [
        "robot_payload.fbs",
    ],
    deps = [
        "//intrinsic/icon/flatbuffers:matrix_types_fbs",
        "//intrinsic/icon/flatbuffers:transform_types_fbs",
    ],
)

cc_flatbuffers_library(
    name = "robot_payload_fbs_cc",
    deps = [":robot_payload_fbs"],
)

cc_library(
    name = "robot_payload_utils",
    srcs = ["robot_payload_utils.cc"],
    hdrs = ["robot_payload_utils.h"],
    deps = [
        ":robot_payload_fbs_cc",
        "//intrinsic/eigenmath",
        "//intrinsic/icon/control/parts:realtime_robot_payload",
        "//intrinsic/icon/flatbuffers:control_types_utils",
        "//intrinsic/icon/flatbuffers:matrix_types_fbs_cc",
        "//intrinsic/icon/flatbuffers:matrix_types_utils",
        "//intrinsic/icon/flatbuffers:transform_types_fbs_cc",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/math:pose3",
        "//intrinsic/world/robot_payload",
        "//intrinsic/world/robot_payload:robot_payload_base",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

flatbuffers_library(
    name = "payload_command_fbs",
    srcs = [
        "payload_command.fbs",
    ],
    deps = [
        ":robot_payload_fbs",
    ],
)

cc_flatbuffers_library(
    name = "payload_command_fbs_cc",
    deps = [":payload_command_fbs"],
)

cc_library(
    name = "payload_command_utils",
    srcs = ["payload_command_utils.cc"],
    hdrs = ["payload_command_utils.h"],
    deps = [
        ":payload_command_fbs_cc",
        ":robot_payload_fbs_cc",
        ":robot_payload_utils",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)

flatbuffers_library(
    name = "payload_state_fbs",
    srcs = [
        "payload_state.fbs",
    ],
    deps = [
        ":robot_payload_fbs",
    ],
)

cc_flatbuffers_library(
    name = "payload_state_fbs_cc",
    deps = [":payload_state_fbs"],
)

cc_library(
    name = "payload_state_utils",
    srcs = ["payload_state_utils.cc"],
    hdrs = ["payload_state_utils.h"],
    deps = [
        ":payload_state_fbs_cc",
        ":robot_payload_fbs_cc",
        ":robot_payload_utils",
        "@com_github_google_flatbuffers//:runtime_cc",
    ],
)
