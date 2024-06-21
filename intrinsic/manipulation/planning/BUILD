# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//intrinsic/manipulation:__subpackages__"])

py_library(
    name = "grasp_planner_client",
    srcs = ["grasp_planner_client.py"],
    deps = [
        "//intrinsic/manipulation/grasping:grasp_execution_planner_params_py_pb2",
        "//intrinsic/manipulation/grasping:grasp_planner_params_py_pb2",
        "//intrinsic/manipulation/grasping:grasp_planning_interfaces",
        "//intrinsic/manipulation/grasping:grasp_py_pb2",
        "//intrinsic/manipulation/service:grasp_planner_service_py_pb2",
        "//intrinsic/manipulation/service:grasp_planner_service_py_pb2_grpc",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
        "@com_google_protobuf//:protobuf_python",
    ],
)
