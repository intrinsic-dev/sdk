# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

package(default_visibility = [
    "//visibility:public",
])

bzl_library(
    name = "cc_fbs_library_bzl",
    srcs = ["cc_fbs_library.bzl"],
    deps = [
        ":fbs_library_bzl",
        "@bazel_skylib//lib:paths",
    ],
)

bzl_library(
    name = "fbs_library_bzl",
    srcs = ["fbs_library.bzl"],
)
