# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "logs",
    srcs = ["logs.go"],
    deps = [
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:cmdutil",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/skills/tools/skill/cmd:imageutil",
        "//intrinsic/skills/tools/skill/cmd:solutionutil",
        "//intrinsic/tools/inctl/auth",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
