# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//intrinsic:public_api_users"])

proto_library(
    name = "solution_service_proto",
    srcs = ["solution_service.proto"],
    deps = [
        ":status_proto",
        "//intrinsic/executive/proto:behavior_tree_proto",
    ],
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
    ],
)

proto_library(
    name = "status_proto",
    srcs = ["status.proto"],
)

go_proto_library(
    name = "status_go_proto",
    deps = [":status_proto"],
)

go_grpc_library(
    name = "status_go_grpc_proto",
    srcs = [":status_proto"],
    deps = [
        "@org_golang_google_protobuf//types/known/timestamppb",
    ],
)
