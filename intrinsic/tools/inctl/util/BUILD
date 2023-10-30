# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "printer",
    srcs = ["printer.go"],
)

go_library(
    name = "cobrautil",
    srcs = ["cobrautil.go"],
    deps = ["@com_github_spf13_cobra//:go_default_library"],
)

go_library(
    name = "templateutil",
    srcs = ["templateutil.go"],
)

go_library(
    name = "color",
    srcs = ["color.go"],
)

go_library(
    name = "viperutil",
    srcs = ["viperutil.go"],
    deps = [
        "@com_github_spf13_pflag//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
    ],
)

go_library(
    name = "orgutil",
    srcs = ["orgutil.go"],
    deps = [
        ":viperutil",
        "//intrinsic/tools/inctl/auth",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
    ],
)
