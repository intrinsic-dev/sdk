# Copyright 2023 Intrinsic Innovation LLC

# This package contains scene features protos for ScenePerception.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "centroid_proto",
    srcs = ["centroid.proto"],
    deps = ["//intrinsic/perception/scene_perception/proto/common:r3_proto"],
)

proto_library(
    name = "damage_proto",
    srcs = ["damage.proto"],
)

proto_library(
    name = "fill_level_proto",
    srcs = ["fill_level.proto"],
)

proto_library(
    name = "graspability_map_proto",
    srcs = ["graspability_map.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
    ],
)

proto_library(
    name = "image_aligned_bounding_box_proto",
    srcs = ["image_aligned_bounding_box.proto"],
)

proto_library(
    name = "image_keypoints_proto",
    srcs = ["image_keypoints.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
    ],
)

proto_library(
    name = "mask_proto",
    srcs = ["mask.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
    ],
)

proto_library(
    name = "mesh_proto",
    srcs = ["mesh.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "point_cloud_proto",
    srcs = ["point_cloud.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "pose_proto",
    srcs = ["pose.proto"],
    deps = [
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "principal_axes_proto",
    srcs = ["principal_axes.proto"],
    deps = [
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "r3_bounding_box_proto",
    srcs = ["r3_bounding_box.proto"],
    deps = [
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "r3_keypoints_proto",
    srcs = ["r3_keypoints.proto"],
    deps = [
        "//intrinsic/math/proto:array_proto",
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "r3_segmented_plane_proto",
    srcs = ["r3_segmented_plane.proto"],
    deps = [
        "//intrinsic/perception/scene_perception/proto/common:r3_proto",
    ],
)

proto_library(
    name = "twist_proto",
    srcs = ["twist.proto"],
    deps = ["//intrinsic/perception/scene_perception/proto/common:r3_proto"],
)

proto_library(
    name = "visibility_proto",
    srcs = ["visibility.proto"],
)

py_proto_library(
    name = "centroid_py_pb2",
    deps = [":centroid_proto"],
)

py_proto_library(
    name = "damage_py_pb2",
    deps = [":damage_proto"],
)

py_proto_library(
    name = "fill_level_py_pb2",
    deps = [":fill_level_proto"],
)

py_proto_library(
    name = "graspability_map_py_pb2",
    deps = [":graspability_map_proto"],
)

py_proto_library(
    name = "image_aligned_bounding_box_py_pb2",
    deps = [":image_aligned_bounding_box_proto"],
)

py_proto_library(
    name = "image_keypoints_py_pb2",
    deps = [":image_keypoints_proto"],
)

py_proto_library(
    name = "mask_py_pb2",
    deps = [":mask_proto"],
)

py_proto_library(
    name = "mesh_py_pb2",
    deps = [":mesh_proto"],
)

py_proto_library(
    name = "point_cloud_py_pb2",
    deps = [":point_cloud_proto"],
)

py_proto_library(
    name = "pose_py_pb2",
    deps = [":pose_proto"],
)

py_proto_library(
    name = "principal_axes_py_pb2",
    deps = [":principal_axes_proto"],
)

py_proto_library(
    name = "r3_bounding_box_py_pb2",
    deps = [":r3_bounding_box_proto"],
)

py_proto_library(
    name = "r3_keypoints_py_pb2",
    deps = [":r3_keypoints_proto"],
)

py_proto_library(
    name = "r3_segmented_plane_py_pb2",
    deps = [":r3_segmented_plane_proto"],
)

py_proto_library(
    name = "twist_py_pb2",
    deps = [":twist_proto"],
)

py_proto_library(
    name = "visibility_py_pb2",
    deps = [":visibility_proto"],
)
