# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "bazel",
    srcs = [
        "bazel.go",
        "bazelinit.go",
    ],
    embedsrcs = [
        "//intrinsic/tools/inctl/cmd/bazel/templates:WORKSPACE.template",  #keep
        "//intrinsic/tools/inctl/cmd/bazel/templates:bazelrc.template",  #keep
        "//intrinsic/tools/inctl/cmd/bazel/templates:bazelversion.template",  #keep
    ],
    visibility = [
        "//intrinsic/skills/tools:__subpackages__",
        "//intrinsic/tools/inctl:__subpackages__",
    ],
    deps = [
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/cmd/version",
        "//intrinsic/tools/inctl/util:cobrautil",
        "//intrinsic/tools/inctl/util:printer",
        "//intrinsic/tools/inctl/util:templateutil",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
