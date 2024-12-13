# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//intrinsic:public_api_users"])

proto_library(
    name = "solution_service_proto",
    srcs = ["solution_service.proto"],
    deps = [
        ":status_proto",
        "//intrinsic/executive/proto:behavior_tree_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

cc_proto_library(
    name = "solution_service_cc_proto",
    deps = [":solution_service_proto"],
)

cc_grpc_library(
    name = "solution_service_cc_grpc_proto",
    srcs = [":solution_service_proto"],
    generate_mocks = True,
    grpc_only = True,
    deps = [":solution_service_cc_proto"],
)

py_proto_library(
    name = "solution_service_py_pb2",
    deps = [":solution_service_proto"],
)

py_grpc_library(
    name = "solution_service_py_pb2_grpc",
    srcs = [":solution_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":solution_service_py_pb2"],
)

go_proto_library(
    name = "solution_service_go_proto",
    go_deps = [
        ":status_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
    ],
    deps = [":solution_service_proto"],
)

go_grpc_library(
    name = "solution_service_go_grpc_proto",
    srcs = [":solution_service_proto"],
    deps = [
        ":status_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "@org_golang_google_protobuf//types/known/emptypb",
    ],
)

proto_library(
    name = "status_proto",
    srcs = ["status.proto"],
)

cc_proto_library(
    name = "status_cc_proto",
    deps = [":status_proto"],
)

py_proto_library(
    name = "status_py_pb2",
    deps = [":status_proto"],
)

go_proto_library(
    name = "status_go_proto",
    deps = [":status_proto"],
)
