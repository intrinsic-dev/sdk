# Copyright 2023 Intrinsic Innovation LLC

# Generic language utilities for golang.

load("//bazel:go_macros.bzl", "go_library", "go_test")

exports_files(
    srcs = [
        # go/keep-sorted start
        "BUILD",
        "xiter.go",
        "xiter_test.go",
        # go/keep-sorted end
    ],
    visibility = ["//intrinsic:release_tooling"],
)

go_library(
    name = "xiter",
    srcs = ["xiter.go"],
    visibility = ["//intrinsic:internal_api_users"],
)

go_test(
    name = "xiter_test",
    srcs = ["xiter_test.go"],
    deps = [
        ":xiter",
        "@com_github_google_go_cmp//cmp:go_default_library",
    ],
)
