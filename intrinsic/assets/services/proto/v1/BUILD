# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "dynamic_reconfiguration_proto",
    srcs = ["dynamic_reconfiguration.proto"],
    deps = ["@com_google_protobuf//:any_proto"],
)

cc_proto_library(
    name = "dynamic_reconfiguration_cc_proto",
    deps = [":dynamic_reconfiguration_proto"],
)

cc_grpc_library(
    name = "dynamic_reconfiguration_cc_grpc_proto",
    srcs = [":dynamic_reconfiguration_proto"],
    grpc_only = True,
    deps = [":dynamic_reconfiguration_cc_proto"],
)

go_proto_library(
    name = "dynamic_reconfiguration_go_proto",
    deps = [":dynamic_reconfiguration_proto"],
)

go_grpc_library(
    name = "dynamic_reconfiguration_go_grpc_proto",
    srcs = [":dynamic_reconfiguration_proto"],
    deps = [
        "@org_golang_google_protobuf//types/known/anypb",
        "@org_golang_google_protobuf//types/known/emptypb",
    ],
)

py_proto_library(
    name = "dynamic_reconfiguration_py_pb2",
    deps = [":dynamic_reconfiguration_proto"],
)

py_grpc_library(
    name = "dynamic_reconfiguration_py_pb2_grpc",
    srcs = [":dynamic_reconfiguration_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":dynamic_reconfiguration_py_pb2"],
)
