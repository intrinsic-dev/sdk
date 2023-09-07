# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@io_bazel_rules_go//go:def.bzl", "go_binary")

package(default_visibility = ["//visibility:public"])

go_binary(
    name = "hwmodule",
    srcs = ["hwmodule.go"],
    deps = [
        "//intrinsic/icon/hal/tools/hwmodule/cmd",
        "//intrinsic/icon/hal/tools/hwmodule/cmd:start",
        "//intrinsic/icon/hal/tools/hwmodule/cmd:stop",
    ],
)
