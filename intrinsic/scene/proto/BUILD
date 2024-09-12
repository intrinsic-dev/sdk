# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "entity_proto",
    srcs = ["entity.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/world/proto:geometry_component_proto",
        "//intrinsic/world/proto:kinematics_component_proto",
        "//intrinsic/world/proto:physics_component_proto",
        "//intrinsic/world/proto:sensor_component_proto",
    ],
)

cc_proto_library(
    name = "entity_cc_proto",
    deps = [
        ":entity_proto",
    ],
)

go_proto_library(
    name = "entity_go_proto",
    go_deps = [
        "//intrinsic/math/proto:pose_go_proto",
        "//intrinsic/world/proto:geometry_component_go_proto",
        "//intrinsic/world/proto:kinematics_component_go_proto",
        "//intrinsic/world/proto:physics_component_go_proto",
        "//intrinsic/world/proto:sensor_component_go_proto",
    ],
    deps = [":entity_proto"],
)

py_proto_library(
    name = "entity_py_pb2",
    visibility = [
        "//visibility:public",
    ],
    deps = [":entity_proto"],
)

proto_library(
    name = "object_properties_proto",
    srcs = ["object_properties.proto"],
)

cc_proto_library(
    name = "object_properties_cc_proto",
    deps = [":object_properties_proto"],
)

go_proto_library(
    name = "object_properties_go_proto",
    deps = [":object_properties_proto"],
)

py_proto_library(
    name = "object_properties_py_pb2",
    visibility = [
        "//visibility:public",
    ],
    deps = [":object_properties_proto"],
)

proto_library(
    name = "scene_object_proto",
    srcs = ["scene_object.proto"],
    deps = [
        ":entity_proto",
        ":object_properties_proto",
        ":simulation_spec_proto",
    ],
)

cc_proto_library(
    name = "scene_object_cc_proto",
    deps = [":scene_object_proto"],
)

go_proto_library(
    name = "scene_object_go_proto",
    go_deps = [
        "//intrinsic/scene/proto:entity_go_proto",
        "//intrinsic/scene/proto:object_properties_go_proto",
        "//intrinsic/scene/proto:simulation_spec_go_proto",
    ],
    deps = [":scene_object_proto"],
)

py_proto_library(
    name = "scene_object_py_pb2",
    visibility = [
        "//visibility:public",
    ],
    deps = [":scene_object_proto"],
)

proto_library(
    name = "scene_object_updates_proto",
    srcs = ["scene_object_updates.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
    ],
)

cc_proto_library(
    name = "scene_object_updates_cc_proto",
    deps = [":scene_object_updates_proto"],
)

go_proto_library(
    name = "scene_object_updates_go_proto",
    go_deps = [
        "//intrinsic/math/proto:pose_go_proto",
    ],
    deps = [":scene_object_updates_proto"],
)

py_proto_library(
    name = "scene_object_updates_py_pb2",
    visibility = [
        "//visibility:public",
    ],
    deps = [":scene_object_updates_proto"],
)

proto_library(
    name = "simulation_spec_proto",
    srcs = ["simulation_spec.proto"],
)

cc_proto_library(
    name = "simulation_spec_cc_proto",
    deps = [":simulation_spec_proto"],
)

go_proto_library(
    name = "simulation_spec_go_proto",
    deps = [":simulation_spec_proto"],
)
