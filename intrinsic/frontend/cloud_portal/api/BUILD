# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//intrinsic/frontend:__subpackages__",
    "//intrinsic/tools/inctl:__subpackages__",
])

proto_library(
    name = "projectdiscovery_api_proto",
    srcs = ["projectdiscovery_api.proto"],
    deps = [
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "projectdiscovery_api_go_proto",
    deps = [":projectdiscovery_api_proto"],
)

go_grpc_library(
    name = "projectdiscovery_api_go_grpc_proto",
    srcs = [":projectdiscovery_api_proto"],
    deps = [
        ":projectdiscovery_api_go_proto",
    ],
)
