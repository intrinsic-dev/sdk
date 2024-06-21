# Copyright 2023 Intrinsic Innovation LLC

# Gripper hardware protos and headers.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "gripper_proto",
    srcs = ["gripper.proto"],
    deps = ["//intrinsic/hardware/proto:settings_proto"],
)

py_proto_library(
    name = "gripper_py_pb2",
    deps = [":gripper_proto"],
)

cc_proto_library(
    name = "gripper_cc_proto",
    deps = [":gripper_proto"],
)
