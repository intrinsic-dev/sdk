# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Libraries related to Realtime Control Layer Parts.

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_arm_part_config_proto",
    srcs = ["hal_arm_part_config.proto"],
    deps = [
        "//intrinsic/icon/control/parts:mode_of_safe_operation_limits_config_proto",
        "//intrinsic/icon/control/parts/hal:hal_part_config_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/icon/proto:joint_position_pid_torque_controller_config_proto",
        "//intrinsic/icon/proto:linear_joint_acceleration_filter_config_proto",
    ],
)
