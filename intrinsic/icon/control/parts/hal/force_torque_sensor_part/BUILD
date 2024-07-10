# Copyright 2023 Intrinsic Innovation LLC

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
