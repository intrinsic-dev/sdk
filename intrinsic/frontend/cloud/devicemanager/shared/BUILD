# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# This folder provides all the files (mostly structs) shared between the cloud side of device management and the on-prem code.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = [
    "//intrinsic/frontend:__subpackages__",
    "//intrinsic/tools/inctl:__subpackages__",
])

go_library(
    name = "shared",
    srcs = ["shared.go"],
)
