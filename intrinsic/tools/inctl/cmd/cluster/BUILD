# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "cluster",
    srcs = [
        "cluster.go",
        "cluster_delete.go",
        "cluster_list.go",
        "cluster_upgrade.go",
    ],
    visibility = [
        "//intrinsic/tools/inctl:__subpackages__",
    ],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdeletion_api_go_proto",
        "//intrinsic/frontend/cloud/api:clusterdeletion_grpc_go_proto",
        "//intrinsic/frontend/cloud/api:clusterdiscovery_api_go_proto",
        "//intrinsic/frontend/cloud/api:clusterdiscovery_grpc_go_proto",
        "//intrinsic/frontend/cloud/updatemanager:info",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/auth",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:cobrautil",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
    ],
)
