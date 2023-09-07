# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library")

# Helper utilities for handling testing.

go_library(
    name = "testio",
    srcs = ["test_io.go"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)
