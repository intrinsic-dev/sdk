# Copyright 2023 Intrinsic Innovation LLC

load("@io_bazel_rules_go//go:def.bzl", "go_binary")

package(default_visibility = ["//visibility:public"])

go_binary(
    name = "inctl_external",
    srcs = ["inctl_external.go"],
    deps = [
        "//intrinsic/assets/services/inctl:service",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/cmd:skill",
        "//intrinsic/tools/inctl/cmd/auth",
        "//intrinsic/tools/inctl/cmd/bazel",
        "//intrinsic/tools/inctl/cmd/cluster",
        "//intrinsic/tools/inctl/cmd/device",
        "//intrinsic/tools/inctl/cmd/notebook",
        "//intrinsic/tools/inctl/cmd/process",
        "//intrinsic/tools/inctl/cmd/solution",
        "//intrinsic/tools/inctl/cmd/version",
    ],
)
