# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_arm_part_config_proto",
    srcs = ["hal_arm_part_config.proto"],
    deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_proto",
        "//intrinsic/icon/control/parts/proto:mode_of_safe_operation_limits_config_proto",
        "//intrinsic/icon/proto:joint_position_pid_torque_controller_config_proto",
        "//intrinsic/icon/proto:linear_joint_acceleration_filter_config_proto",
    ],
)

go_proto_library(
    name = "hal_arm_part_config_go_proto",
    go_deps = [
        "//intrinsic/icon/control/parts/proto:mode_of_safe_operation_limits_config_go_proto",
        "//intrinsic/icon/control/parts/hal:hal_part_config_go_proto",
        "//intrinsic/icon/proto:joint_position_pid_torque_controller_config_go_proto",
        "//intrinsic/icon/proto:linear_joint_acceleration_filter_config_go_proto",
    ],
    visibility = [
        "//intrinsic:__subpackages__",
    ],
    deps = [":hal_arm_part_config_proto"],
)

cc_proto_library(
    name = "hal_arm_part_config_cc_proto",
    visibility = [
        "//intrinsic/icon:__subpackages__",
    ],
    deps = [":hal_arm_part_config_proto"],
)
