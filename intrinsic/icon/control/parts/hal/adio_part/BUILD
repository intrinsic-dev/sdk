# Copyright 2023 Intrinsic Innovation LLC

# Libraries related to Realtime Control Layer Parts.

load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hal_adio_part_config_proto",
    srcs = ["hal_adio_part_config.proto"],
    deps = ["//intrinsic/icon/control/parts/hal:hal_part_config_proto"],
)

go_proto_library(
    name = "hal_adio_part_config_go_proto",
    go_deps = [
        "//intrinsic/icon/control/parts/hal:hal_part_config_go_proto",
    ],
    visibility = ["//visibility:private"],
    deps = [":hal_adio_part_config_proto"],
)
