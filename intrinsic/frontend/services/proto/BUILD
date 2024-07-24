# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//intrinsic:public_api_users"])

proto_library(
    name = "processes_service_proto",
    srcs = ["processes_service.proto"],
    deps = ["//intrinsic/executive/proto:behavior_tree_proto"],
)

go_proto_library(
    name = "processes_service_go_proto",
    go_deps = [
        "//intrinsic/executive/proto:behavior_tree_go_proto",
    ],
    deps = [":processes_service_proto"],
)

go_grpc_library(
    name = "processes_service_go_grpc_proto",
    srcs = [":processes_service_proto"],
    deps = [
        "//intrinsic/executive/proto:behavior_tree_go_proto",
    ],
)
