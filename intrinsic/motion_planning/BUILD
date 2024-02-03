# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "motion_planner_client",
    srcs = ["motion_planner_client.cc"],
    hdrs = ["motion_planner_client.h"],
    deps = [
        ":conversions",
        "//intrinsic/eigenmath",
        "//intrinsic/geometry/proto:shape_data_cc_proto",
        "//intrinsic/icon/proto:cart_space_conversion",
        "//intrinsic/icon/proto:joint_space_cc_proto",
        "//intrinsic/kinematics/types:cartesian_limits",
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/motion_planning/proto:motion_planner_config_cc_proto",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_grpc_proto",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_proto",
        "//intrinsic/motion_planning/proto:motion_specification_cc_proto",
        "//intrinsic/motion_planning/proto:motion_target_cc_proto",
        "//intrinsic/util:eigen",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/objects:kinematic_object",
        "//intrinsic/world/objects:transform_node",
        "//intrinsic/world/proto:collision_settings_cc_proto",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/status:statusor",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "motion_planner_client_py",
    srcs = ["motion_planner_client.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/motion_planning/proto:motion_planner_service_py_pb2",
        "//intrinsic/motion_planning/proto:motion_planner_service_py_pb2_grpc",
        "//intrinsic/motion_planning/proto:motion_specification_py_pb2",
        "//intrinsic/motion_planning/proto:motion_target_py_pb2",
        "//intrinsic/world/proto:collision_settings_py_pb2",
        "//intrinsic/world/proto:geometric_constraints_py_pb2",
        "//intrinsic/world/python:object_world_ids",
        requirement("grpcio"),
    ],
)

cc_library(
    name = "conversions",
    srcs = ["conversions.cc"],
    hdrs = ["conversions.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/proto:joint_space_cc_proto",
        "//intrinsic/util:eigen",
        "@com_google_protobuf//:protobuf_lite",
    ],
)
