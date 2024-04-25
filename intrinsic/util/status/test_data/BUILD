# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(
    default_visibility = [
        "//intrinsic/util/status:__subpackages__",
    ],
)

proto_library(
    name = "test_service_proto",
    srcs = ["test_service.proto"],
    deps = ["@com_google_protobuf//:empty_proto"],
)

go_proto_library(
    name = "test_service_go_proto",
    deps = [":test_service_proto"],
)

go_grpc_library(
    name = "test_service_go_grpc_proto",
    srcs = [":test_service_proto"],
    deps = [
        "@org_golang_google_protobuf//types/known/emptypb",
    ],
)
