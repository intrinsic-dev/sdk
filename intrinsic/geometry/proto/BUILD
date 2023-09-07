# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

""" Intrinsic package geometry/proto. """

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "axis_aligned_bounding_box_proto",
    srcs = ["axis_aligned_bounding_box.proto"],
    deps = [
        "//intrinsic/math/proto:vector2_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

cc_proto_library(
    name = "axis_aligned_bounding_box_cc_proto",
    deps = [":axis_aligned_bounding_box_proto"],
)

py_proto_library(
    name = "axis_aligned_bounding_box_py_pb2",
    deps = [":axis_aligned_bounding_box_proto"],
)

proto_library(
    name = "oriented_bounding_box_proto",
    srcs = ["oriented_bounding_box.proto"],
    deps = [
        ":axis_aligned_bounding_box_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

py_proto_library(
    name = "oriented_bounding_box_py_pb2",
    deps = [":oriented_bounding_box_proto"],
)

cc_proto_library(
    name = "oriented_bounding_box_cc_proto",
    deps = [":oriented_bounding_box_proto"],
)

proto_library(
    name = "geometry_proto",
    srcs = ["geometry.proto"],
    deps = [
        ":lazy_exact_geometry_proto",
        ":renderable_proto",
    ],
)

cc_proto_library(
    name = "geometry_cc_proto",
    deps = [":geometry_proto"],
)

py_proto_library(
    name = "geometry_py_pb2",
    deps = [":geometry_proto"],
)

proto_library(
    name = "lazy_exact_geometry_proto",
    srcs = ["lazy_exact_geometry.proto"],
    deps = [
        ":mesh_octree_wrapping_proto",
        ":primitives_proto",
        ":triangle_mesh_proto",
    ],
)

cc_proto_library(
    name = "lazy_exact_geometry_cc_proto",
    deps = [":lazy_exact_geometry_proto"],
)

py_proto_library(
    name = "lazy_exact_geometry_py_pb2",
    deps = [":lazy_exact_geometry_proto"],
)

proto_library(
    name = "mesh_octree_wrapping_proto",
    srcs = ["mesh_octree_wrapping.proto"],
    deps = [":octree_proto"],
)

cc_proto_library(
    name = "mesh_octree_wrapping_cc_proto",
    deps = [":mesh_octree_wrapping_proto"],
)

py_proto_library(
    name = "mesh_octree_wrapping_py_pb2",
    deps = [":mesh_octree_wrapping_proto"],
)

proto_library(
    name = "octree_proto",
    srcs = ["octree.proto"],
    deps = [":axis_aligned_bounding_box_proto"],
)

cc_proto_library(
    name = "octree_cc_proto",
    deps = [":octree_proto"],
)

py_proto_library(
    name = "octree_py_pb2",
    deps = [":octree_proto"],
)

proto_library(
    name = "primitives_proto",
    srcs = ["primitives.proto"],
    deps = ["//intrinsic/math/proto:vector3_proto"],
)

cc_proto_library(
    name = "primitives_cc_proto",
    deps = [":primitives_proto"],
)

py_proto_library(
    name = "primitives_py_pb2",
    deps = [":primitives_proto"],
)

proto_library(
    name = "renderable_proto",
    srcs = ["renderable.proto"],
)

cc_proto_library(
    name = "renderable_cc_proto",
    deps = [":renderable_proto"],
)

py_proto_library(
    name = "renderable_py_pb2",
    deps = [":renderable_proto"],
)

proto_library(
    name = "shape_data_proto",
    srcs = ["shape_data.proto"],
    deps = ["//intrinsic/math/proto:matrix_proto"],
)

cc_proto_library(
    name = "shape_data_cc_proto",
    deps = [":shape_data_proto"],
)

py_proto_library(
    name = "shape_data_py_pb2",
    deps = [":shape_data_proto"],
)

go_proto_library(
    name = "shape_data_go_proto",
    go_deps = [
        "//intrinsic/math/proto:matrix_go_proto",
    ],
    deps = [":shape_data_proto"],
)

proto_library(
    name = "triangle_mesh_proto",
    srcs = ["triangle_mesh.proto"],
)

cc_proto_library(
    name = "triangle_mesh_cc_proto",
    deps = [":triangle_mesh_proto"],
)

py_proto_library(
    name = "triangle_mesh_py_pb2",
    deps = [":triangle_mesh_proto"],
)
