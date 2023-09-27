# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Package containing test utilities for gRPC.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:private"])

proto_library(
    name = "ping_proto",
    srcs = ["ping.proto"],
    deps = [
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "ping_go_proto",
    deps = [":ping_proto"],
)

go_grpc_library(
    name = "ping_go_grpc_proto",
    srcs = [":ping_proto"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@org_golang_google_protobuf//types/known/emptypb:go_default_library",
    ],
)

py_proto_library(
    name = "ping_proto_py_pb2",
    deps = [":ping_proto"],
)

py_grpc_library(
    name = "ping_proto_py_pb2_grpc",
    srcs = [":ping_proto"],
    grpc_library = requirement("grpcio"),
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":ping_proto_py_pb2"],
)
