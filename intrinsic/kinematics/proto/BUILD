# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "kinematics_proto",
    srcs = ["kinematics.proto"],
    deps = [
        "//intrinsic/math/proto:matrix_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

cc_proto_library(
    name = "kinematics_cc_proto",
    deps = [":kinematics_proto"],
)

py_proto_library(
    name = "kinematics_py_proto",
    deps = [":kinematics_proto"],
)

proto_library(
    name = "skeleton_proto",
    srcs = ["skeleton.proto"],
    deps = [
        ":kinematics_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

cc_proto_library(
    name = "skeleton_cc_proto",
    deps = [":skeleton_proto"],
)

py_proto_library(
    name = "skeleton_py_proto",
    deps = [":skeleton_proto"],
)
