# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//intrinsic/assets:__subpackages__",
    "//intrinsic/frontend:__subpackages__",
    "//intrinsic/kubernetes:__subpackages__",
    "//intrinsic/skills/tools/skill:__subpackages__",
    "//intrinsic/solutions:__subpackages__",
    "//intrinsic/tools/inctl:__subpackages__",
])

proto_library(
    name = "clustermanager_api_proto",
    srcs = ["clustermanager_api.proto"],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdeletion_api_proto",
        "//intrinsic/util/status:extended_status_proto",
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options_proto",
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_googleapis//google/api:field_behavior_proto",
        "@com_google_googleapis//google/longrunning:operations_proto",
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:field_mask_proto",
    ],
)

go_proto_library(
    name = "clustermanager_api_go_proto",
    go_deps = [
        "@org_golang_google_genproto_googleapis_api//annotations",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "//intrinsic/frontend/cloud/api:clusterdeletion_api_go_grpc_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options",
    ],
    deps = [":clustermanager_api_proto"],
)

go_grpc_library(
    name = "clustermanager_api_go_grpc_proto",
    srcs = [":clustermanager_api_proto"],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdeletion_api_go_grpc_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
)
