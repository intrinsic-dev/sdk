# Copyright 2023 Intrinsic Innovation LLC

# Package containing integration tests for Intrinsic.

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load("//bazel:go_macros.bzl", "go_library")

bzl_library(
    name = "build_defs_bzl",
    srcs = ["build_defs.bzl"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/testing/dockerized_test_executor:delegated_test",
    ],
)

go_library(
    name = "grpctest",
    srcs = ["grpctest.go"],
    visibility = [
        "//intrinsic:__subpackages__",
    ],
    deps = [
        "@com_github_bazelbuild_remote_apis_sdks//go/pkg/portpicker",
    ],
)
