# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "service",
    srcs = ["service.go"],
    deps = [
        ":install",
        ":list",
        "//intrinsic/tools/inctl/cmd:root",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "install",
    srcs = ["install.go"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "//intrinsic/skills/tools/resource/cmd:bundleimages",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/auth",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "list",
    srcs = ["list.go"],
    deps = [
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/resources/proto:resource_registry_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
