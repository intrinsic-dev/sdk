# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "dio_config_proto",
    srcs = ["dio_config.proto"],
)

cc_proto_library(
    name = "dio_config_cc_proto",
    deps = [":dio_config_proto"],
)

go_proto_library(
    name = "dio_config_go_proto",
    deps = [":dio_config_proto"],
)

proto_library(
    name = "services_config_proto",
    srcs = ["services_config.proto"],
)

cc_proto_library(
    name = "services_config_cc_proto",
    deps = [":services_config_proto"],
)

go_proto_library(
    name = "services_config_go_proto",
    deps = [":services_config_proto"],
)

proto_library(
    name = "icon_main_config_proto",
    srcs = ["icon_main_config.proto"],
    deps = [
        ":realtime_control_config_proto",
        ":services_config_proto",
    ],
)

cc_proto_library(
    name = "icon_main_config_cc_proto",
    deps = [":icon_main_config_proto"],
)

go_proto_library(
    name = "icon_main_config_go_proto",
    go_deps = [
        ":realtime_control_config_go_proto",
        ":services_config_go_proto",
    ],
    deps = [":icon_main_config_proto"],
)

proto_library(
    name = "realtime_control_config_proto",
    srcs = ["realtime_control_config.proto"],
    deps = [
        "//intrinsic/icon/control/parts:realtime_part_config_proto",
        "//intrinsic/icon/control/parts/hal:hal_part_config_proto",
    ],
)

cc_proto_library(
    name = "realtime_control_config_cc_proto",
    deps = [":realtime_control_config_proto"],
)

go_proto_library(
    name = "realtime_control_config_go_proto",
    go_deps = [
        "//intrinsic/icon/control/parts:realtime_part_config_go_proto",
        "//intrinsic/icon/control/parts/hal:hal_part_config_go_proto",
    ],
    visibility = ["//intrinsic/resources:__subpackages__"],
    deps = [":realtime_control_config_proto"],
)
