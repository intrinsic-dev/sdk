# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//intrinsic/frontend/cloud/api:__subpackages__",
    "//intrinsic/frontend/cloud/devicemanager:__subpackages__",
    "//intrinsic/kubernetes/api_relay/cloud:__subpackages__",
    "//intrinsic/kubernetes/intrinsic_base:__subpackages__",
    "//intrinsic/production:__subpackages__",
    "//intrinsic/tools/inctl/cmd:__subpackages__",
])

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
