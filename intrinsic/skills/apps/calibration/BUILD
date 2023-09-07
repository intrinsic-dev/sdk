# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Skills for calibration of cameras and the workcell.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "collect_calibration_data_proto",
    srcs = ["collect_calibration_data.proto"],
    deps = [
        ":sample_calibration_poses_proto",
        "//intrinsic/perception/proto:hand_eye_calibration",
        "//intrinsic/perception/proto:pattern_detection_config",
        "//intrinsic/perception/proto:pose_estimator_id_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

cc_proto_library(
    name = "collect_calibration_data_cc_proto",
    deps = [":collect_calibration_data_proto"],
)

py_proto_library(
    name = "collect_calibration_data_py_pb2",
    deps = [":collect_calibration_data_proto"],
)

proto_library(
    name = "sample_calibration_poses_proto",
    srcs = ["sample_calibration_poses.proto"],
    deps = [
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/motion_planning/proto:motion_target_proto",
        "//intrinsic/skills/proto:skills_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

cc_proto_library(
    name = "sample_calibration_poses_cc_proto",
    deps = [":sample_calibration_poses_proto"],
)

py_proto_library(
    name = "sample_calibration_poses_py_pb2",
    deps = [":sample_calibration_poses_proto"],
)

proto_library(
    name = "optimize_robot_and_camera_poses_proto",
    srcs = ["optimize_robot_and_camera_poses.proto"],
    deps = ["//intrinsic/math/proto:pose_proto"],
)

py_proto_library(
    name = "optimize_robot_and_camera_poses_py_pb2",
    deps = [":optimize_robot_and_camera_poses_proto"],
)

cc_proto_library(
    name = "optimize_robot_and_camera_poses_cc_proto",
    deps = [":optimize_robot_and_camera_poses_proto"],
)
