# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "channel_factory",
    srcs = ["channel_factory.cc"],
    hdrs = ["channel_factory.h"],
    deps = [
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:channel_interface",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "equipment_utils",
    srcs = ["equipment_utils.cc"],
    hdrs = ["equipment_utils.h"],
    deps = [
        ":channel_factory",
        ":icon_equipment_cc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_utils",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/grpc:channel_interface",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:optional",
    ],
)

proto_library(
    name = "icon_equipment_proto",
    srcs = ["icon_equipment.proto"],
    deps = [
        ":force_control_settings_proto",
    ],
)

cc_proto_library(
    name = "icon_equipment_cc_proto",
    deps = [":icon_equipment_proto"],
)

py_proto_library(
    name = "icon_equipment_py_pb2",
    deps = [":icon_equipment_proto"],
)

proto_library(
    name = "force_control_settings_proto",
    srcs = ["force_control_settings.proto"],
    deps = ["//intrinsic/icon/proto:cart_space_proto"],
)

go_proto_library(
    name = "force_control_settings_go_proto",
    go_deps = [
        "//intrinsic/icon/proto:cart_space_go_proto",
    ],
    deps = [":force_control_settings_proto"],
)

cc_proto_library(
    name = "force_control_settings_cc_proto",
    deps = [":force_control_settings_proto"],
)

py_proto_library(
    name = "force_control_settings_py_pb2",
    deps = [":force_control_settings_proto"],
)

py_library(
    name = "equipment_utils_py",
    srcs = ["equipment_utils.py"],
    deps = [
        ":icon_equipment_py_pb2",
        "//intrinsic/icon/python:icon",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/proto:equipment_py_pb2",
        "//intrinsic/util/grpc:connection",
        "@com_google_absl_py//absl/logging",
    ],
)
