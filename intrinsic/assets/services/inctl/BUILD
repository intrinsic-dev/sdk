# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "service",
    srcs = ["service.go"],
    deps = [
        ":add",
        ":delete",
        ":install",
        ":list",
        ":uninstall",
        "//intrinsic/tools/inctl/cmd:root",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "add",
    srcs = ["add.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:version",
        "//intrinsic/assets/proto:asset_deployment_go_grpc_proto",
        "//intrinsic/assets/proto:asset_type_go_proto",
        "//intrinsic/resources/proto:resource_registry_go_grpc_proto",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)

go_library(
    name = "delete",
    srcs = ["delete.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets/proto:asset_deployment_go_grpc_proto",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
    ],
)

go_library(
    name = "install",
    srcs = ["install.go"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "//intrinsic/skills/tools/resource/cmd:bundleimages",
        "//intrinsic/skills/tools/skill/cmd/directupload",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "list",
    srcs = ["list.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/resources/proto:resource_registry_go_grpc_proto",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "uninstall",
    srcs = ["uninstall.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:version",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "//intrinsic/resources/proto:resource_registry_go_grpc_proto",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
