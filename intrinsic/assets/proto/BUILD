# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

proto_library(
    name = "tag_proto",
    srcs = ["tag.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

go_proto_library(
    name = "tag_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":tag_proto"],
)

proto_library(
    name = "view_proto",
    srcs = ["view.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

go_proto_library(
    name = "view_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":view_proto"],
)

proto_library(
    name = "id_proto",
    srcs = ["id.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

py_proto_library(
    name = "id_py_pb2",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":id_proto"],
)

cc_proto_library(
    name = "id_cc_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":id_proto"],
)

go_proto_library(
    name = "id_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":id_proto"],
)

proto_library(
    name = "vendor_proto",
    srcs = ["vendor.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

py_proto_library(
    name = "vendor_py_pb2",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":vendor_proto"],
)

cc_proto_library(
    name = "vendor_cc_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":vendor_proto"],
)

go_proto_library(
    name = "vendor_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":vendor_proto"],
)

proto_library(
    name = "documentation_proto",
    srcs = ["documentation.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

cc_proto_library(
    name = "documentation_cc_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":documentation_proto"],
)

py_proto_library(
    name = "documentation_py_pb2",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":documentation_proto"],
)

go_proto_library(
    name = "documentation_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":documentation_proto"],
)
