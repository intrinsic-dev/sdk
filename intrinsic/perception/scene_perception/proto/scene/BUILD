# Copyright 2023 Intrinsic Innovation LLC

# This package contains scene protos for ScenePerception.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "structured_faces_proto",
    srcs = ["structured_faces.proto"],
    deps = [
        ":structured_features_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

proto_library(
    name = "structured_features_proto",
    srcs = ["structured_features.proto"],
    deps = [
        "//intrinsic/perception/scene_perception/proto/scene/features:centroid_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:damage_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:fill_level_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:graspability_map_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:image_aligned_bounding_box_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:image_keypoints_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:mask_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:mesh_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:point_cloud_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:pose_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:principal_axes_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:r3_bounding_box_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:r3_keypoints_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:r3_segmented_plane_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:twist_proto",
        "//intrinsic/perception/scene_perception/proto/scene/features:visibility_proto",
    ],
)

proto_library(
    name = "structured_objects_proto",
    srcs = ["structured_objects.proto"],
    deps = [
        ":structured_faces_proto",
        ":structured_features_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

proto_library(
    name = "pickled_scene_proto",
    srcs = ["pickled_scene.proto"],
)

proto_library(
    name = "structured_scene_proto",
    srcs = ["structured_scene.proto"],
    deps = [
        ":structured_features_proto",
        ":structured_objects_proto",
        "//intrinsic/perception/scene_perception/proto/common:camera_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

proto_library(
    name = "scene_container_proto",
    srcs = ["scene_container.proto"],
    deps = [
        ":pickled_scene_proto",
        ":structured_scene_proto",
    ],
)

py_proto_library(
    name = "scene_container_py_pb2",
    deps = [":scene_container_proto"],
)
