# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

# This package contains the tools to handle tar archives.

package(default_visibility = ["//visibility:private"])

exports_files(
    srcs = [
        # go/keep-sorted start
        "BUILD",
        "tartooling.go",
        "tartooling_test.go",
        "untar.cc",
        "untar.go",
        "untar.h",
        "untar_test.cc",
        # go/keep-sorted end
    ],
    visibility = ["//visibility:public"],
)

go_library(
    name = "tartooling",
    srcs = ["tartooling.go"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "untar",
    srcs = ["untar.go"],
    visibility = ["//intrinsic:__subpackages__"],
)
