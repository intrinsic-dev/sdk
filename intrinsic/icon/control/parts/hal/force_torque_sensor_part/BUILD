# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_force_torque_sensor_part_config_proto",
    srcs = ["hal_force_torque_sensor_part_config.proto"],
    deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_proto",
        "//intrinsic/icon/equipment:force_control_settings_proto",
        "//intrinsic/icon/proto:linear_joint_acceleration_filter_config_proto",
    ],
)

go_proto_library(
    name = "hal_force_torque_sensor_part_config_go_proto",
    go_deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_go_proto",
        "//intrinsic/icon/equipment:force_control_settings_go_proto",
        "//intrinsic/icon/proto:linear_joint_acceleration_filter_config_go_proto",
    ],
    deps = [":hal_force_torque_sensor_part_config_proto"],
)

cc_proto_library(
    name = "hal_force_torque_sensor_part_config_cc_proto",
    deps = [":hal_force_torque_sensor_part_config_proto"],
)
