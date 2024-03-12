# Copyright 2023 Intrinsic Innovation LLC

# The device manager allows to configure specific devices and facilitates the onboarding flow for new installations.

load("//bazel:go_macros.bzl", "go_library")

go_library(
    name = "info",
    srcs = ["info.go"],
    visibility = [
        "//intrinsic/frontend/cloud/api:__pkg__",
        "//intrinsic/tools/inctl/cmd/cluster:__pkg__",
    ],
)

go_library(
    name = "messages",
    srcs = ["messages.go"],
    visibility = [
        "//intrinsic/tools/inctl/cmd/cluster:__pkg__",
    ],
)
