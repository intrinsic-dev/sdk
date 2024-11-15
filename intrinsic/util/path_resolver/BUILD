# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library", "go_test")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "pathresolver",  # Coding style suggests to avoid using underscores in package names: http://golang.org/doc/effective_go.html#package-names
    srcs = ["path_resolver.go"],
    deps = [
        "@io_bazel_rules_go//go/runfiles:go_default_library",
    ],
)

go_test(
    name = "path_resolver_go_test",
    srcs = ["path_resolver_test.go"],
    data = ["path_resolver_test.go"],
    deps = [":pathresolver"],
)
