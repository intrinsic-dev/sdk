# Copyright 2023 Intrinsic Innovation LLC

# Shared Bazel macros for use in external workspaces and general Bazel helpers.

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

package(default_visibility = ["//visibility:public"])

exports_files(glob(["content_mirror/*"]))

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
        "container-image": "docker://gcr.io/cloud-robotics-releases/bazel-rbe-executor@sha256:fffa413a7fb1506c6e78e12fa7506ae92e35840af033c7ce0bb9d8ffbb0163a8",
        "OSFamily": "Linux",
    },
    parents = ["@local_config_platform//:host"],
)
