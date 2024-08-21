# Copyright 2023 Intrinsic Innovation LLC

# Shared Bazel macros for use in external workspaces and general Bazel helpers.

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

package(default_visibility = ["//visibility:public"])

exports_files(glob(["content_mirror/*"]))

bzl_library(
    name = "go_macros",
    srcs = ["go_macros.bzl"],
)

bzl_library(
    name = "label",
    srcs = ["label.bzl"],
)

exports_files(
    srcs = ["deps_0.bzl"],
    visibility = ["//intrinsic/production/external:__pkg__"],
)

platform(
    name = "linux_x86_64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
        "@bazel_tools//tools/cpp:clang",
    ],
    exec_properties = {
        "container-image": "docker://gcr.io/cloud-robotics-releases/bazel-rbe-executor@sha256:babf055ff655acb4125d47a1d9e14c67f49755c83c2a4f0588453e171b2b93aa",
        "OSFamily": "Linux",
    },
    parents = ["@local_config_platform//:host"],
)
