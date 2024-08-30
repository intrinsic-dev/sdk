# Copyright 2023 Intrinsic Innovation LLC

# An acl engine using Authzed SpiceDB.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = [
    "//visibility:public",
])

go_library(
    name = "jwt",
    srcs = ["jwt.go"],
    deps = ["@com_github_pkg_errors//:go_default_library"],
)
