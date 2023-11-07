# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "resource_handle_proto",
    srcs = ["resource_handle.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "resource_handle_cc_proto",
    deps = [":resource_handle_proto"],
)

py_proto_library(
    name = "resource_handle_py_pb2",
    deps = [":resource_handle_proto"],
)

go_proto_library(
    name = "resource_handle_go_proto",
    deps = [":resource_handle_proto"],
)
