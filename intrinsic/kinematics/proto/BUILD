# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

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

go_proto_library(
    name = "kinematics_go_proto",
    go_deps = [
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
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

go_proto_library(
    name = "skeleton_go_proto",
    go_deps = [
        ":kinematics_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
    deps = [":skeleton_proto"],
)
