# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "channel_factory",
    srcs = ["channel_factory.cc"],
    hdrs = ["channel_factory.h"],
    deps = [
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:channel_interface",
        "//intrinsic/util/grpc:connection_params",
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
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_utils",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/grpc:channel_interface",
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
    visibility = ["//visibility:private"],
)

cc_proto_library(
    name = "icon_equipment_cc_proto",
    visibility = ["//visibility:private"],
    deps = [":icon_equipment_proto"],
)

py_proto_library(
    name = "icon_equipment_py_pb2",
    deps = [":icon_equipment_proto"],
)

py_library(
    name = "equipment_utils_py",
    srcs = ["equipment_utils.py"],
    deps = [
        ":icon_equipment_py_pb2",
        "//intrinsic/icon/python:icon",
        "//intrinsic/skills/proto:equipment_py_pb2",
        "//intrinsic/util/grpc:connection",
        "@com_google_absl_py//absl/logging",
    ],
)
