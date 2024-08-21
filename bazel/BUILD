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
        "container-image": "docker://gcr.io/cloud-robotics-releases/bazel-rbe-executor@sha256:3ee043e7a322caaff8c9edaa302373deb80e67ad6e42ae35d34b8f3597b8995e",
        "OSFamily": "Linux",
    },
    parents = ["@local_config_platform//:host"],
)
