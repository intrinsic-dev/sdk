# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library", "go_test")
load("@io_bazel_rules_docker//container:container.bzl", "container_image")

package(default_visibility = [
    "//visibility:public",
])

go_library(
    name = "intrinsic",
    srcs = ["init.go"],
)
