# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "solution",
    srcs = [
        "solution.go",
        "solution_get.go",
        "solution_list.go",
    ],
    visibility = [
        "//intrinsic/skills/tools:__subpackages__",
        "//intrinsic/tools/inctl:__subpackages__",
    ],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdiscovery_grpc_go_proto",
        "//intrinsic/frontend/cloud/api:solutiondiscovery_grpc_go_proto",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
    ],
)
