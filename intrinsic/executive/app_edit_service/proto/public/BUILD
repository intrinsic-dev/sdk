# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Contains public proto files of the app_edit_service.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = [
    "//intrinsic/executive/app_edit_service:__subpackages__",
    "//intrinsic/solutions:__subpackages__",
])

exports_files(
    srcs = glob(["*.proto"]) + ["BUILD"],
    visibility = ["//intrinsic/production:__subpackages__"],
)

proto_library(
    name = "app_edit_service_proto",
    srcs = ["app_edit_service.proto"],
    deps = [
        "//intrinsic/config/proto:ppr_refs_proto",
        "//intrinsic/executive/proto:behavior_tree_proto",
    ],
)

py_proto_library(
    name = "app_edit_service_py_pb2",
    deps = [":app_edit_service_proto"],
)

py_grpc_library(
    name = "app_edit_service_py_pb2_grpc",
    srcs = [":app_edit_service_proto"],
    deps = [":app_edit_service_py_pb2"],
)
