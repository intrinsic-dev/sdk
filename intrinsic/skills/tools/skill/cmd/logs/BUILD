# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "logs",
    srcs = ["logs.go"],
    deps = [
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/assets:imageutils",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/skills/tools/skill/cmd:solutionutil",
        "//intrinsic/tools/inctl/auth",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
