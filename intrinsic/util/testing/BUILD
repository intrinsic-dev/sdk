# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

# Helper utilities for handling testing.

go_library(
    name = "testio",
    srcs = ["test_io.go"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@io_bazel_rules_go//go/tools/bazel:go_default_library",
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

cc_library(
    name = "gtest_wrapper",
    testonly = 1,
    hdrs = ["gtest_wrapper.h"],
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_inazarenko_protobuf_matchers//protobuf-matchers",
        "@com_google_cel_cpp//internal:testing",
        "@com_google_googletest//:gtest_main",
    ],
)
