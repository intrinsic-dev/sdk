# Copyright 2023 Intrinsic Innovation LLC

# Services for the manipulation package.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//intrinsic/manipulation:__subpackages__"])

proto_library(
    name = "grasp_planner_service_proto",
    srcs = ["grasp_planner_service.proto"],
    deps = [
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/manipulation/grasping:grasp_execution_planner_params_proto",
        "//intrinsic/manipulation/grasping:grasp_planner_params_proto",
        "//intrinsic/manipulation/grasping:grasp_proto",
        "//intrinsic/manipulation/proto:workspace_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

py_proto_library(
    name = "grasp_planner_service_py_pb2",
    deps = [":grasp_planner_service_proto"],
)

py_grpc_library(
    name = "grasp_planner_service_py_pb2_grpc",
    srcs = [":grasp_planner_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":grasp_planner_service_py_pb2"],
)
