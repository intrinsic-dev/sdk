# Copyright 2023 Intrinsic Innovation LLC

# This package contains common protos for ScenePerception.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "camera_proto",
    srcs = ["camera.proto"],
    deps = [
        ":r3_proto",
        "//intrinsic/perception/proto:frame_proto",
    ],
)

proto_library(
    name = "error_proto",
    srcs = ["error.proto"],
)

proto_library(
    name = "message_proto",
    srcs = ["message.proto"],
)

proto_library(
    name = "r3_proto",
    srcs = ["r3.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:quaternion_proto",
        "//intrinsic/math/proto:twist_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

py_proto_library(
    name = "camera_py_pb2",
    deps = [":camera_proto"],
)

py_proto_library(
    name = "error_py_pb2",
    deps = [":error_proto"],
)

py_proto_library(
    name = "message_py_pb2",
    deps = [":message_proto"],
)

py_proto_library(
    name = "r3_py_pb2",
    deps = [":r3_proto"],
)
