# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_imu_part_config_proto",
    srcs = ["hal_imu_part_config.proto"],
    deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

go_proto_library(
    name = "hal_imu_part_config_go_proto",
    go_deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
    visibility = ["//visibility:private"],
    deps = [":hal_imu_part_config_proto"],
)

cc_proto_library(
    name = "hal_imu_part_config_cc_proto",
    deps = [":hal_imu_part_config_proto"],
)
