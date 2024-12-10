# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library", "go_test")

# This package contains the tools to handle tar archives.

package(default_visibility = ["//visibility:private"])

go_library(
    name = "tartooling",
    srcs = ["tartooling.go"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_test(
    name = "tartooling_test",
    srcs = ["tartooling_test.go"],
    library = ":tartooling",
    deps = [
        "//intrinsic/util/proto/testing:diamond_a_go_proto",
        "@com_github_google_go_cmp//cmp:go_default_library",
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//testing/protocmp:go_default_library",
    ],
)

go_library(
    name = "untar",
    srcs = ["untar.go"],
    visibility = ["//intrinsic:__subpackages__"],
)
