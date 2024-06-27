# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "cleardefault",
    srcs = ["cleardefault.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/catalog/proto:skill_catalog_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
