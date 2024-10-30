# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

proto_library(
    name = "kvstore_proto",
    srcs = ["kvstore.proto"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@com_google_protobuf//:any_proto",
    ],
)

exports_files(
    ["kvservice.yaml"],
    visibility = ["//intrinsic:__subpackages__"],
)

go_proto_library(
    name = "kvstore_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":kvstore_proto"],
)

cc_proto_library(
    name = "kvstore_cc_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":kvstore_proto"],
)

cc_grpc_library(
    name = "kvstore_cc_grpc_proto",
    srcs = [":kvstore_proto"],
    grpc_only = True,
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":kvstore_cc_proto"],
)

py_proto_library(
    name = "kvstore_py_pb2",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":kvstore_proto"],
)
