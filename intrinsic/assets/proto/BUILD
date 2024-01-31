# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

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
    name = "view_proto",
    srcs = ["view.proto"],
)

go_proto_library(
    name = "view_go_proto",
    deps = [":view_proto"],
)

proto_library(
    name = "id_proto",
    srcs = ["id.proto"],
)

py_proto_library(
    name = "id_py_pb2",
    deps = [":id_proto"],
)

cc_proto_library(
    name = "id_cc_proto",
    deps = [":id_proto"],
)

go_proto_library(
    name = "id_go_proto",
    deps = [":id_proto"],
)

proto_library(
    name = "vendor_proto",
    srcs = ["vendor.proto"],
)

py_proto_library(
    name = "vendor_py_pb2",
    deps = [":vendor_proto"],
)

cc_proto_library(
    name = "vendor_cc_proto",
    deps = [":vendor_proto"],
)

go_proto_library(
    name = "vendor_go_proto",
    deps = [":vendor_proto"],
)

proto_library(
    name = "documentation_proto",
    srcs = ["documentation.proto"],
)

cc_proto_library(
    name = "documentation_cc_proto",
    deps = [":documentation_proto"],
)

py_proto_library(
    name = "documentation_py_pb2",
    deps = [":documentation_proto"],
)

go_proto_library(
    name = "documentation_go_proto",
    deps = [":documentation_proto"],
)
