# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_grpc_library", "go_library", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "admin_api_proto",
    srcs = ["admin_api.proto"],
    deps = [
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "admin_api_go_proto",
    deps = [":admin_api_proto"],
)

go_grpc_library(
    name = "admin_go_grpc_proto",
    srcs = [":admin_api_proto"],
    deps = [":admin_api_go_proto"],
)

proto_library(
    name = "tokensv1api_proto",
    srcs = ["tokensv1_api.proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options_proto",
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "tokensv1api_go_proto",
    go_deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
    deps = [":tokensv1api_proto"],
)

go_grpc_library(
    name = "tokensv1api_go_grpc_proto",
    srcs = [":tokensv1api_proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
)

proto_library(
    name = "orgsv1api_proto",
    srcs = ["orgsv1_api.proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options_proto",
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_googleapis//google/longrunning:operations_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "orgsv1api_go_proto",
    go_deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options",
        "@org_golang_google_genproto_googleapis_api//annotations",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
    ],
    deps = [":orgsv1api_proto"],
)

go_grpc_library(
    name = "orgsv1api_go_grpc_proto",
    srcs = [":orgsv1api_proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
)

proto_library(
    name = "discoveryv1api_proto",
    srcs = ["discoveryv1_api.proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options_proto",
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "discoveryv1api_go_proto",
    go_deps = [
        "@org_golang_google_genproto_googleapis_api//annotations",
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options:options",
    ],
    deps = [
        ":discoveryv1api_proto",
    ],
)

go_grpc_library(
    name = "discoveryv1api_go_grpc_proto",
    srcs = [":discoveryv1api_proto"],
    deps = [
        "@com_github_grpc_ecosystem_grpc_gateway_v2//protoc-gen-openapiv2/options",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
)

go_library(
    name = "clients",
    srcs = ["clients.go"],
    importpath = "intrinsic/kubernetes/accounts/service/api",
    deps = [
        ":admin_go_grpc_proto",
        ":discoveryv1api_go_grpc_proto",
        ":orgsv1api_go_grpc_proto",
        ":tokensv1api_go_grpc_proto",
        "//intrinsic/frontend/go:cloudserver",
        "//intrinsic/kubernetes/acl:serviceauth",
        "@io_opencensus_go//plugin/ocgrpc:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials:go_default_library",
    ],
)

go_library(
    name = "clientstubs",
    testonly = True,
    srcs = ["clientstubs.go"],
    importpath = "intrinsic/kubernetes/accounts/service/api",
    deps = [
        ":tokensv1api_go_grpc_proto",
        ":tokensv1api_go_proto",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//types/known/emptypb",
    ],
)
