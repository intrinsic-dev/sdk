# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "cmd",
    srcs = ["root.go"],
    deps = [
        "//intrinsic/tools/inctl/cmd:root",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "solutionutil",
    srcs = ["solutionutil.go"],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdiscovery_api_go_grpc_proto",
        "//intrinsic/tools/inctl/cmd/solution",
        "@org_golang_google_grpc//:go_default_library",
    ],
)

go_library(
    name = "registry",
    srcs = ["registry.go"],
    deps = [
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/assets:imageutils",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
    ],
)

go_library(
    name = "dialerutil",
    srcs = ["dialerutil.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/tools/inctl/auth",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)

go_library(
    name = "waitforskill",
    srcs = ["waitforskill.go"],
    deps = [
        "//intrinsic/skills/proto:skill_registry_go_grpc_proto",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)

go_library(
    name = "listutil",
    srcs = ["listutil.go"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/catalog/proto:skill_catalog_go_grpc_proto",
        "//intrinsic/skills/proto:skills_go_proto",
    ],
)
