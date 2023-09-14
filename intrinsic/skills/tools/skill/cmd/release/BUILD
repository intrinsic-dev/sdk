# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "release",
    srcs = ["release.go"],
    deps = [
        "//intrinsic/assets/proto:tag_go_proto",
        "//intrinsic/skills/catalog/proto:skill_catalog_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:cmdutil",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/skills/tools/skill/cmd:imagetransfer",
        "//intrinsic/skills/tools/skill/cmd:imageutil",
        "//intrinsic/skills/tools/skill/cmd:registry",
        "@com_github_google_go_containerregistry//pkg/authn:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/google:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
    ],
)
