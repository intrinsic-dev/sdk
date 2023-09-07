# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "version",
    srcs = ["version.go"],
    visibility = [
        "//intrinsic/skills/tools:__subpackages__",
        "//intrinsic/tools/inctl:__subpackages__",
    ],
    x_defs = {"SDKVersion": "{STABLE_SDK_VERSION}"},
    deps = [
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
