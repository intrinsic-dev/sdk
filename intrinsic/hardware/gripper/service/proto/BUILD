# Copyright 2023 Intrinsic Innovation LLC

# This package contains internal proto definition required for implementing the
# pinch gripper service.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "generic_gripper_proto",
    srcs = ["generic_gripper.proto"],
)

cc_proto_library(
    name = "generic_gripper_cc_proto",
    deps = [":generic_gripper_proto"],
)

cc_grpc_library(
    name = "generic_gripper_cc_grpc_proto",
    srcs = [":generic_gripper_proto"],
    generate_mocks = True,
    grpc_only = True,
    deps = [":generic_gripper_cc_proto"],
)

py_proto_library(
    name = "generic_gripper_py_pb2",
    deps = [":generic_gripper_proto"],
)

go_proto_library(
    name = "generic_gripper_go_proto",
    deps = [":generic_gripper_proto"],
)

py_grpc_library(
    name = "generic_gripper_py_pb2_grpc",
    srcs = [":generic_gripper_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":generic_gripper_py_pb2"],
)
