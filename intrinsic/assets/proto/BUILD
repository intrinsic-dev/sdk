# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "tag_proto",
    srcs = ["tag.proto"],
)

go_proto_library(
    name = "tag_go_proto",
    deps = [":tag_proto"],
)

proto_library(
    name = "id_proto",
    srcs = ["id.proto"],
)

cc_proto_library(
    name = "id_cc_proto",
    deps = [":id_proto"],
)

go_proto_library(
    name = "id_go_proto",
    deps = [":id_proto"],
)
