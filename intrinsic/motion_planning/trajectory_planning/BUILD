# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "blended_joint_move_proto",
    srcs = ["blended_joint_move.proto"],
    deps = [
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

cc_proto_library(
    name = "blended_joint_move_cc_proto",
    deps = [":blended_joint_move_proto"],
)

py_proto_library(
    name = "blended_joint_move_py_pb2",
    deps = [":blended_joint_move_proto"],
)
