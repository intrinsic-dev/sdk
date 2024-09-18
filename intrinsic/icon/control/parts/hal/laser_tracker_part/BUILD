# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_laser_tracker_part_config_proto",
    srcs = ["hal_laser_tracker_part_config.proto"],
    deps = ["//intrinsic/icon/control/parts/hal:hal_part_config_proto"],
)

cc_proto_library(
    name = "hal_laser_tracker_part_config_cc_proto",
    deps = [":hal_laser_tracker_part_config_proto"],
)
