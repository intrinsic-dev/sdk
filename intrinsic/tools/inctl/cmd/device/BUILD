# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "device",
    srcs = [
        "config.go",
        "device.go",
        "register.go",
    ],
    deps = [
        ":projectclient",
        "//intrinsic/frontend/cloud/devicemanager/shared",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/tools/inctl/util:printer",
        "//intrinsic/tools/inctl/util:viperutil",
        "@com_github_cenkalti_backoff_v4//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
        "@org_uber_go_multierr//:go_default_library",
    ],
)

go_library(
    name = "projectclient",
    srcs = ["projectclient.go"],
    deps = [
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/auth",
    ],
)
