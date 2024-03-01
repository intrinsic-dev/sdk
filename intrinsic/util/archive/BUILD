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
        "testdata/untar/abspath.tar",
        "testdata/untar/floor.tar",
        "testdata/untar/floor/1_one/nothingwrongwith.me",
        "testdata/untar/floor/2_two/nothingwrongwith.me",
        "testdata/untar/floor/3_three/nothingwrongwith.me",
        "testdata/untar/floor/4_four/nothingwrongwith.me",
        "testdata/untar/relpath.tar",
        "testdata/untar/symlink.tar",
        "testdata/untar/symlink_user.tar",
        "untar.cc",
        "untar.go",
        "untar.h",
        "untar_test.cc",
        # go/keep-sorted end
    ],
    visibility = ["//intrinsic/production:__subpackages__"],
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
