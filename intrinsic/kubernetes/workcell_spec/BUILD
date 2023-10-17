# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

go_library(
    name = "imagetags",
    srcs = [
        "imagetags.go",
    ],
    visibility = [
        "//intrinsic/icon/hal/tools:__subpackages__",
        "//intrinsic/production:__subpackages__",
        "//intrinsic/skills/tools:__subpackages__",
    ],
    deps = [
        "@com_github_pborman_uuid//:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
    ],
)
