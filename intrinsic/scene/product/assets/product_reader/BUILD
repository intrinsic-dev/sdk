# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "product_reader_proto",
    srcs = ["product_reader.proto"],
    deps = [
        "//intrinsic/scene/product/proto:product_proto",
        "//intrinsic/scene/proto:scene_object_proto",
        "@com_google_protobuf//:struct_proto",
    ],
)

py_proto_library(
    name = "product_reader_py_pb2",
    deps = [":product_reader_proto"],
)

py_grpc_library(
    name = "product_reader_py_pb2_grpc",
    srcs = [":product_reader_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":product_reader_py_pb2"],
)

cc_proto_library(
    name = "product_reader_cc_proto",
    deps = [":product_reader_proto"],
)

cc_grpc_library(
    name = "product_reader_cc_grpc",
    srcs = [":product_reader_proto"],
    grpc_only = True,
    deps = [":product_reader_cc_proto"],
)
