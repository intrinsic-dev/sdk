# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Generic functionality for all hal parts.

load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_part_config_proto",
    srcs = ["hal_part_config.proto"],
)

cc_proto_library(
    name = "hal_part_config_cc_proto",
    deps = [":hal_part_config_proto"],
)

go_proto_library(
    name = "hal_part_config_go_proto",
    deps = [":hal_part_config_proto"],
)

# Required so that mainloop resource instances can be configured for every HAL part.
proto_library(
    name = "hal_part_config_types_for_mainloop",
    deps = [
        ":hal_part_config_proto",
        "//intrinsic/icon/control/parts/hal/adio_part:hal_adio_part_config_proto",
        "//intrinsic/icon/control/parts/hal/arm_part:hal_arm_part_config_proto",
        "//intrinsic/icon/control/parts/hal/force_torque_sensor_part:hal_force_torque_sensor_part_config_proto",
        "//intrinsic/icon/control/parts/hal/imu_part:hal_imu_part_config_proto",
        "//intrinsic/icon/control/parts/hal/linear_gripper_part:hal_linear_gripper_part_config_proto",
        "//intrinsic/icon/control/parts/hal/rangefinder_part:hal_rangefinder_part_config_proto",
    ],
)
