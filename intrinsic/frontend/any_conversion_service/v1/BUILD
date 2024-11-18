# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//intrinsic:public_api_users"])

proto_library(
    name = "any_conversion_service_proto",
    srcs = ["any_conversion_service.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:descriptor_proto",
    ],
)

go_proto_library(
    name = "any_conversion_service_go_proto",
    deps = [":any_conversion_service_proto"],
)

go_grpc_library(
    name = "any_conversion_service_go_grpc_proto",
    srcs = [":any_conversion_service_proto"],
    deps = [
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)
