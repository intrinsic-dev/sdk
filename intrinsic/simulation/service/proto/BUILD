# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Protos for the simulation service.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "simulation_service_proto",
    srcs = [
        "simulation_service.proto",
    ],
    deps = [
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:wrappers_proto",
    ],
)

cc_proto_library(
    name = "simulation_service_cc_proto",
    deps = [":simulation_service_proto"],
)

cc_grpc_library(
    name = "simulation_service_cc_grpc_proto",
    srcs = [":simulation_service_proto"],
    grpc_only = True,
    deps = [":simulation_service_cc_proto"],
)

py_proto_library(
    name = "simulation_service_py_pb2",
    deps = [":simulation_service_proto"],
)

py_grpc_library(
    name = "simulation_service_py_pb2_grpc",
    srcs = [":simulation_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":simulation_service_py_pb2"],
)
