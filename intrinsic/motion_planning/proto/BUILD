# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "motion_planner_service_proto",
    srcs = ["motion_planner_service.proto"],
    deps = [
        ":motion_planner_config_proto",
        ":motion_specification_proto",
        ":motion_target_proto",
        "//intrinsic/geometry/proto:shape_data_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/logging/proto:context_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/world/proto:collision_settings_proto",
        "//intrinsic/world/proto:geometric_constraints_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

cc_proto_library(
    name = "motion_planner_service_cc_proto",
    deps = [":motion_planner_service_proto"],
)

cc_grpc_library(
    name = "motion_planner_service_cc_grpc_proto",
    srcs = [":motion_planner_service_proto"],
    grpc_only = True,
    deps = [":motion_planner_service_cc_proto"],
)

py_proto_library(
    name = "motion_planner_service_py_pb2",
    deps = [":motion_planner_service_proto"],
)

py_grpc_library(
    name = "motion_planner_service_py_pb2_grpc",
    srcs = [":motion_planner_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":motion_planner_service_py_pb2"],
)

proto_library(
    name = "motion_target_proto",
    srcs = ["motion_target.proto"],
    deps = [
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/kinematics/ik/constrained:constrained_ik_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

cc_proto_library(
    name = "motion_target_cc_proto",
    deps = [":motion_target_proto"],
)

py_proto_library(
    name = "motion_target_py_pb2",
    deps = [":motion_target_proto"],
)

proto_library(
    name = "motion_specification_proto",
    srcs = ["motion_specification.proto"],
    deps = [
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/world/proto:collision_settings_proto",
        "//intrinsic/world/proto:geometric_constraints_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

proto_library(
    name = "motion_planner_config_proto",
    srcs = ["motion_planner_config.proto"],
    deps = ["@com_google_protobuf//:duration_proto"],
)

cc_proto_library(
    name = "motion_planner_config_cc_proto",
    deps = [":motion_planner_config_proto"],
)

py_proto_library(
    name = "motion_planner_config_py_pb2",
    deps = [":motion_planner_config_proto"],
)

go_proto_library(
    name = "motion_planner_config_go_proto",
    deps = [":motion_planner_config_proto"],
)

cc_proto_library(
    name = "motion_specification_cc_proto",
    deps = [":motion_specification_proto"],
)

py_proto_library(
    name = "motion_specification_py_pb2",
    deps = [":motion_specification_proto"],
)
