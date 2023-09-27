# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Shared Bazel macros for use in external workspaces and general Bazel helpers.

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load(":label_test.bzl", "label_test_suite")

package(default_visibility = ["//visibility:public"])

label_test_suite()

bzl_library(
    name = "label",
    srcs = ["label.bzl"],
)

exports_files(
    srcs = ["deps_0.bzl"],
    visibility = ["//intrinsic/production/external:__pkg__"],
)
