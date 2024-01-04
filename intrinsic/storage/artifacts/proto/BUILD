# Copyright 2023 Intrinsic Innovation LLC

# gRPC service definition for the workcell-spec-service.

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "artifact_proto",
    srcs = ["artifact.proto"],
    deps = ["@com_google_protobuf//:timestamp_proto"],
)

go_proto_library(
    name = "artifact_go_proto",
    deps = [":artifact_proto"],
)

go_grpc_library(
    name = "artifact_go_grpc_proto",
    srcs = [":artifact_proto"],
    deps = [":artifact_go_proto"],
)
