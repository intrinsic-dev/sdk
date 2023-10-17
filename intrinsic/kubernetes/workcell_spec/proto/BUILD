# Copyright 2023 Intrinsic Innovation LLC

# gRPC service definition for the workcell-spec-service.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "image_proto",
    srcs = ["image.proto"],
)

go_proto_library(
    name = "image_go_proto",
    deps = [":image_proto"],
)

py_proto_library(
    name = "image_py_pb2",
    deps = [":image_proto"],
)

proto_library(
    name = "installer_proto",
    srcs = ["installer.proto"],
    deps = [
        ":image_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

go_proto_library(
    name = "installer_go_proto",
    go_deps = [":image_go_proto"],
    deps = [":installer_proto"],
)

go_grpc_library(
    name = "installer_go_grpc_proto",
    srcs = [":installer_proto"],
    deps = [
        ":image_go_proto",
        ":installer_go_proto",
    ],
)

py_proto_library(
    name = "installer_py_pb2",
    deps = [":installer_proto"],
)

py_grpc_library(
    name = "installer_py_pb2_grpc",
    srcs = [":installer_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":installer_py_pb2"],
)
