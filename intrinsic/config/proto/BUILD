# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "ppr_refs_proto",
    srcs = ["ppr_refs.proto"],
)

cc_proto_library(
    name = "ppr_refs_cc_proto",
    deps = [":ppr_refs_proto"],
)

go_proto_library(
    name = "ppr_refs_go_proto",
    deps = [":ppr_refs_proto"],
)

py_proto_library(
    name = "ppr_refs_py_pb2",
    deps = [":ppr_refs_proto"],
)
