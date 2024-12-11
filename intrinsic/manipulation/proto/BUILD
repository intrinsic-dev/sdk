# Copyright 2023 Intrinsic Innovation LLC

# Commonly used protos for manipulation

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "workspace_proto",
    srcs = ["workspace.proto"],
    deps = [
        "//intrinsic/geometry/proto:oriented_bounding_box_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

py_proto_library(
    name = "workspace_py_pb2",
    deps = [":workspace_proto"],
)

cc_proto_library(
    name = "workspace_cc_proto",
    deps = [":workspace_proto"],
)
