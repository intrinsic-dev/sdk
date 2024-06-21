# Copyright 2023 Intrinsic Innovation LLC

""" Intrinsic package grasping.

This includes grasping related protos, grasp planning service and grasp skills."""

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

cc_proto_library(
    name = "grasp_cc_proto",
    deps = [":grasp_proto"],
)

proto_library(
    name = "grasp_annotations_proto",
    srcs = ["grasp_annotations.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

proto_library(
    name = "grasp_proto",
    srcs = ["grasp.proto"],
    deps = [
        "//intrinsic/hardware/gripper:gripper_proto",
        "//intrinsic/hardware/gripper/eoat:eoat_service_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/world/proto:geometric_constraints_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

py_proto_library(
    name = "grasp_py_pb2",
    deps = [":grasp_proto"],
)

py_library(
    name = "grasp_planning_interfaces",
    srcs = ["grasp_planning_interfaces.py"],
    deps = [
        ":grasp_py_pb2",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/perception/scene_perception/proto/scene:scene_container_py_pb2",
        "//intrinsic/world/proto:geometric_constraints_py_pb2",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/python:object_world_client",
    ],
)

proto_library(
    name = "grasp_execution_planner_params_proto",
    srcs = ["grasp_execution_planner_params.proto"],
    deps = ["//intrinsic/motion_planning/proto:motion_specification_proto"],
)

py_proto_library(
    name = "grasp_execution_planner_params_py_pb2",
    deps = [":grasp_execution_planner_params_proto"],
)

proto_library(
    name = "grasp_planner_params_proto",
    srcs = ["grasp_planner_params.proto"],
    deps = [
        ":grasp_adapter_params_proto",
        ":grasp_proto",
        ":grasp_ranker_params_proto",
        "//intrinsic/manipulation/proto:workspace_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

py_proto_library(
    name = "grasp_planner_params_py_pb2",
    deps = [":grasp_planner_params_proto"],
)

proto_library(
    name = "grasp_ranker_params_proto",
    srcs = ["grasp_ranker_params.proto"],
    deps = [
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
    ],
)

proto_library(
    name = "grasp_adapter_params_proto",
    srcs = ["grasp_adapter_params.proto"],
)
