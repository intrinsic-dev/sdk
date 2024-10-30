# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "sim_bus_hardware_module_proto",
    srcs = ["sim_bus_hardware_module.proto"],
    deps = [
        "//intrinsic/icon/server/config:dio_config_proto",
        "//intrinsic/simulation/gazebo/plugins:sim_hardware_module_config_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

go_proto_library(
    name = "sim_bus_hardware_module_go_proto",
    go_deps = [
        "//intrinsic/icon/server/config:dio_config_go_proto",
        "//intrinsic/simulation/gazebo/plugins:sim_hardware_module_config_go_proto",
    ],
    deps = [":sim_bus_hardware_module_proto"],
)

cc_proto_library(
    name = "sim_bus_hardware_module_cc_proto",
    deps = [":sim_bus_hardware_module_proto"],
)
