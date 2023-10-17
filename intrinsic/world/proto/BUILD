# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "collision_action_proto",
    srcs = ["collision_action.proto"],
)

cc_proto_library(
    name = "collision_action_cc_proto",
    deps = [":collision_action_proto"],
)

py_proto_library(
    name = "collision_action_py_pb2",
    deps = [":collision_action_proto"],
)

go_proto_library(
    name = "collision_action_go_proto",
    deps = [":collision_action_proto"],
)

proto_library(
    name = "collision_settings_proto",
    srcs = ["collision_settings.proto"],
    deps = [
        ":collision_action_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

cc_proto_library(
    name = "collision_settings_cc_proto",
    deps = [":collision_settings_proto"],
)

py_proto_library(
    name = "collision_settings_py_pb2",
    deps = [":collision_settings_proto"],
)

go_proto_library(
    name = "collision_settings_go_proto",
    go_deps = [
        ":collision_action_go_proto",
        ":object_world_refs_go_proto",
    ],
    deps = [":collision_settings_proto"],
)

proto_library(
    name = "geometry_component_proto",
    srcs = ["geometry_component.proto"],
    deps = [
        "//intrinsic/math/proto:matrix_proto",
        "//intrinsic/math/proto:point_proto",
    ],
)

cc_proto_library(
    name = "geometry_component_cc_proto",
    deps = [":geometry_component_proto"],
)

py_proto_library(
    name = "geometry_component_py_pb2",
    deps = [":geometry_component_proto"],
)

go_proto_library(
    name = "geometry_component_go_proto",
    go_deps = [
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
    ],
    deps = [":geometry_component_proto"],
)

proto_library(
    name = "kinematics_component_proto",
    srcs = ["kinematics_component.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

cc_proto_library(
    name = "kinematics_component_cc_proto",
    deps = [":kinematics_component_proto"],
)

go_proto_library(
    name = "kinematics_component_go_proto",
    go_deps = [
        "//intrinsic/math/proto:vector3_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
    deps = [":kinematics_component_proto"],
)

proto_library(
    name = "object_world_refs_proto",
    srcs = ["object_world_refs.proto"],
)

cc_proto_library(
    name = "object_world_refs_cc_proto",
    deps = [":object_world_refs_proto"],
)

py_proto_library(
    name = "object_world_refs_py_pb2",
    deps = [":object_world_refs_proto"],
)

go_proto_library(
    name = "object_world_refs_go_proto",
    deps = [":object_world_refs_proto"],
)

proto_library(
    name = "object_world_service_proto",
    srcs = ["object_world_service.proto"],
    deps = [
        ":collision_action_proto",
        ":collision_settings_proto",
        ":geometry_component_proto",
        ":kinematics_component_proto",
        ":object_world_refs_proto",
        ":object_world_updates_proto",
        ":physics_component_proto",
        ":simulation_component_proto",
        ":spawner_component_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/skills/proto:footprint_proto",
        "@com_google_googleapis//google/rpc:status_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "object_world_service_cc_proto",
    deps = [":object_world_service_proto"],
)

cc_grpc_library(
    name = "object_world_service_cc_grpc_proto",
    srcs = [":object_world_service_proto"],
    grpc_only = True,
    deps = [":object_world_service_cc_proto"],
)

py_proto_library(
    name = "object_world_service_py_pb2",
    deps = [":object_world_service_proto"],
)

py_grpc_library(
    name = "object_world_service_py_pb2_grpc",
    srcs = [":object_world_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":object_world_service_py_pb2"],
)

proto_library(
    name = "object_world_updates_proto",
    srcs = ["object_world_updates.proto"],
    deps = [
        ":collision_action_proto",
        ":collision_settings_proto",
        ":geometry_component_proto",
        ":object_world_refs_proto",
        ":physics_component_proto",
        ":simulation_component_proto",
        ":spawner_component_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/math/proto:pose_proto",
        "@com_google_protobuf//:wrappers_proto",
    ],
)

cc_proto_library(
    name = "object_world_updates_cc_proto",
    deps = [":object_world_updates_proto"],
)

py_proto_library(
    name = "object_world_updates_py_pb2",
    deps = [":object_world_updates_proto"],
)

proto_library(
    name = "physics_component_proto",
    srcs = ["physics_component.proto"],
    deps = [
        "//intrinsic/math/proto:matrix_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

py_proto_library(
    name = "physics_component_py_pb2",
    deps = [":physics_component_proto"],
)

cc_proto_library(
    name = "physics_component_cc_proto",
    deps = [":physics_component_proto"],
)

go_proto_library(
    name = "physics_component_go_proto",
    go_deps = [
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
    deps = [":physics_component_proto"],
)

proto_library(
    name = "simulation_component_proto",
    srcs = ["simulation_component.proto"],
)

py_proto_library(
    name = "simulation_component_py_pb2",
    deps = [":simulation_component_proto"],
)

cc_proto_library(
    name = "simulation_component_cc_proto",
    deps = [":simulation_component_proto"],
)

go_proto_library(
    name = "simulation_component_go_proto",
    deps = [":simulation_component_proto"],
)

proto_library(
    name = "spawner_component_proto",
    srcs = ["spawner_component.proto"],
    deps = [
        "//intrinsic/math/proto:vector3_proto",
    ],
)

py_proto_library(
    name = "spawner_component_py_pb2",
    deps = [":spawner_component_proto"],
)

cc_proto_library(
    name = "spawner_component_cc_proto",
    deps = [":spawner_component_proto"],
)

go_proto_library(
    name = "spawner_component_go_proto",
    go_deps = [
        "//intrinsic/math/proto:vector3_go_proto",
    ],
    deps = [":spawner_component_proto"],
)

proto_library(
    name = "geometric_constraints_proto",
    srcs = ["geometric_constraints.proto"],
    deps = [
        ":object_world_refs_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:quaternion_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

cc_proto_library(
    name = "geometric_constraints_cc_proto",
    deps = [":geometric_constraints_proto"],
)

py_proto_library(
    name = "geometric_constraints_py_pb2",
    deps = [":geometric_constraints_proto"],
)

py_proto_library(
    name = "entity_search_py_pb2",
    deps = [":entity_search_proto"],
)

proto_library(
    name = "world_protos",
    deps = [
        ":geometric_constraints_proto",
        ":geometry_component_proto",
        ":kinematics_component_proto",
        ":object_world_refs_proto",
        ":object_world_service_proto",
        ":physics_component_proto",
        ":simulation_component_proto",
        ":spawner_component_proto",
        "//intrinsic/world/proto:entity_search_proto",
    ],
)

proto_library(
    name = "entity_search_proto",
    srcs = ["entity_search.proto"],
)
