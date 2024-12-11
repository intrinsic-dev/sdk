# Copyright 2023 Intrinsic Innovation LLC

# Plugins for modeling equipment behaviors in Gazebo simulation.

load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "sim_hardware_module_config_proto",
    srcs = ["sim_hardware_module_config.proto"],
)

go_proto_library(
    name = "sim_hardware_module_config_go_proto",
    deps = [":sim_hardware_module_config_proto"],
)

cc_proto_library(
    name = "sim_hardware_module_config_cc_proto",
    deps = [":sim_hardware_module_config_proto"],
)
