# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(default_visibility = ["//intrinsic:public_api_users"])

proto_library(
    name = "inversion_proto",
    srcs = ["inversion.proto"],
)

go_proto_library(
    name = "inversion_go_proto",
    deps = [":inversion_proto"],
)

go_grpc_library(
    name = "inversion_go_grpc_proto",
    srcs = [":inversion_proto"],
)

proto_source_code_info_transitive_descriptor_set(
    name = "inversion_proto_descriptor_set",
    deps = [":inversion_proto"],
)
