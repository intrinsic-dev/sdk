# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "auth",
    srcs = ["auth.go"],
)

go_library(
    name = "authtest",
    testonly = True,
    srcs = ["authtest.go"],
    deps = [":auth"],
)
