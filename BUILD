# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_gazelle//:def.bzl", "gazelle")

gazelle(name = "gazelle")

exports_files(
    srcs = [
        ".bazelrc",
        ".bazelversion",
    ],
    visibility = ["//intrinsic/tools/inctl/cmd/bazel/templates:__subpackages__"],
)

exports_files(
    srcs = [
        "requirements.in",
        "requirements.txt",
    ],
    visibility = ["//intrinsic/production/external:__pkg__"],
)
