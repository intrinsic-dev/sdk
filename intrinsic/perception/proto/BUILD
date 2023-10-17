# Copyright 2023 Intrinsic Innovation LLC

# This package contains public protos that are exposed to clients of Intrinsic perception.

load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "camera_params_proto",
    srcs = ["camera_params.proto"],
    deps = [
        ":distortion_params_proto",
        ":intrinsic_params_proto",
    ],
)

py_proto_library(
    name = "camera_params_py_pb2",
    deps = [":camera_params_proto"],
)

proto_library(
    name = "dimensions_proto",
    srcs = ["dimensions.proto"],
)

go_proto_library(
    name = "dimensions_go_proto",
    deps = [":dimensions_proto"],
)

proto_library(
    name = "distortion_params_proto",
    srcs = ["distortion_params.proto"],
)

cc_proto_library(
    name = "distortion_params_cc_proto",
    deps = [":distortion_params_proto"],
)

py_proto_library(
    name = "distortion_params_py_pb2",
    deps = [":distortion_params_proto"],
)

go_proto_library(
    name = "distortion_params_go_proto",
    deps = [":distortion_params_proto"],
)

proto_library(
    name = "frame_proto",
    srcs = ["frame.proto"],
    deps = [
        ":camera_params_proto",
        ":image_buffer_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "frame_cc_proto",
    deps = [":frame_proto"],
)

py_proto_library(
    name = "frame_py_pb2",
    deps = [":frame_proto"],
)

proto_library(
    name = "frame_post_processing_proto",
    srcs = ["frame_post_processing.proto"],
    deps = [
        ":dimensions_proto",
        ":image_buffer_proto",
    ],
)

py_proto_library(
    name = "frame_post_processing_py_pb2",
    deps = [":frame_post_processing_proto"],
)

proto_library(
    name = "intrinsic_params_proto",
    srcs = ["intrinsic_params.proto"],
    deps = [":dimensions_proto"],
)

cc_proto_library(
    name = "intrinsic_params_cc_proto",
    deps = [":intrinsic_params_proto"],
)

py_proto_library(
    name = "intrinsic_params_py_pb2",
    deps = [":intrinsic_params_proto"],
)

go_proto_library(
    name = "intrinsic_params_go_proto",
    go_deps = [":dimensions_go_proto"],
    deps = [":intrinsic_params_proto"],
)

proto_library(
    name = "pose_estimation_result",
    srcs = ["pose_estimation_result.proto"],
    deps = [
        ":image_buffer_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

proto_library(
    name = "hand_eye_calibration",
    srcs = ["hand_eye_calibration.proto"],
    deps = [
        ":intrinsic_calibration_proto",
        ":pattern_detection_result",
        "//intrinsic/math/proto:pose_proto",
    ],
)

proto_library(
    name = "image_buffer_proto",
    srcs = ["image_buffer.proto"],
    deps = [":dimensions_proto"],
)

proto_library(
    name = "camera_drivers_proto",
    srcs = ["camera_drivers.proto"],
)

cc_proto_library(
    name = "camera_drivers_cc_proto",
    deps = [":camera_drivers_proto"],
)

py_proto_library(
    name = "camera_drivers_py_pb2",
    deps = [":camera_drivers_proto"],
)

go_proto_library(
    name = "camera_drivers_go_proto",
    deps = [":camera_drivers_proto"],
)

go_grpc_library(
    name = "camera_drivers_go_grpc_proto",
    srcs = [":camera_drivers_proto"],
    deps = [":camera_drivers_go_proto"],
)

proto_library(
    name = "camera_identifier_proto",
    srcs = ["camera_identifier.proto"],
    deps = [
        ":camera_drivers_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "camera_identifier_cc_proto",
    deps = [":camera_identifier_proto"],
)

py_proto_library(
    name = "camera_identifier_py_pb2",
    deps = [":camera_identifier_proto"],
)

go_proto_library(
    name = "camera_identifier_go_proto",
    go_deps = [":camera_drivers_go_proto"],
    deps = [":camera_identifier_proto"],
)

go_grpc_library(
    name = "camera_identifier_go_grpc_proto",
    srcs = [":camera_identifier_proto"],
    deps = [
        ":camera_drivers_go_proto",
        ":camera_identifier_go_proto",
    ],
)

proto_library(
    name = "camera_config",
    srcs = ["camera_config.proto"],
    deps = [
        ":camera_identifier_proto",
        ":camera_settings_proto",
        ":distortion_params_proto",
        ":intrinsic_params_proto",
        ":sensor_config",
    ],
)

py_proto_library(
    name = "camera_config_py_pb2",
    deps = [":camera_config"],
)

cc_proto_library(
    name = "camera_config_cc_proto",
    deps = ["camera_config"],
)

go_proto_library(
    name = "camera_config_go_proto",
    go_deps = [
        ":camera_identifier_go_proto",
        ":camera_settings_go_proto",
        ":distortion_params_go_proto",
        ":intrinsic_params_go_proto",
        ":sensor_config_go_proto",
    ],
    deps = [":camera_config"],
)

proto_library(
    name = "sensor_config",
    srcs = ["sensor_config.proto"],
    deps = [
        ":camera_settings_proto",
        ":distortion_params_proto",
        ":intrinsic_params_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

py_proto_library(
    name = "sensor_config_py_pb2",
    deps = [":sensor_config"],
)

cc_proto_library(
    name = "sensor_config_cc_proto",
    deps = ["sensor_config"],
)

go_proto_library(
    name = "sensor_config_go_proto",
    go_deps = [
        ":camera_settings_go_proto",
        ":distortion_params_go_proto",
        ":intrinsic_params_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
    ],
    deps = [":sensor_config"],
)

proto_library(
    name = "sensor_image",
    srcs = ["sensor_image.proto"],
    deps = [
        ":image_buffer_proto",
        ":sensor_config",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

py_proto_library(
    name = "sensor_image_py_pb2",
    deps = [":sensor_image"],
)

cc_proto_library(
    name = "sensor_image_cc_proto",
    deps = ["sensor_image"],
)

proto_library(
    name = "capture_result_proto",
    srcs = ["capture_result.proto"],
    deps = [
        ":sensor_image",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "capture_result_cc_proto",
    deps = [":capture_result_proto"],
)

py_proto_library(
    name = "capture_result_py_pb2",
    deps = [":capture_result_proto"],
)

proto_library(
    name = "camera_settings_proto",
    srcs = ["camera_settings.proto"],
    deps = [
        "//intrinsic/hardware/proto:settings_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

py_proto_library(
    name = "camera_settings_py_pb2",
    deps = [":camera_settings_proto"],
)

cc_proto_library(
    name = "camera_settings_cc_proto",
    deps = [":camera_settings_proto"],
)

go_proto_library(
    name = "camera_settings_go_proto",
    go_deps = ["//intrinsic/hardware/proto:settings_go_proto"],
    deps = [":camera_settings_proto"],
)

go_grpc_library(
    name = "camera_settings_go_grpc_proto",
    srcs = [":camera_settings_proto"],
    deps = [
        ":camera_settings_go_proto",
        "//intrinsic/hardware/proto:settings_go_proto",
    ],
)

py_proto_library(
    name = "image_buffer_py_pb2",
    deps = [":image_buffer_proto"],
)

proto_library(
    name = "intrinsic_calibration_proto",
    srcs = ["intrinsic_calibration.proto"],
    deps = [
        ":camera_params_proto",
        ":dimensions_proto",
        ":pattern_detection_result",
    ],
)

py_proto_library(
    name = "intrinsic_calibration_py_pb2",
    deps = [":intrinsic_calibration_proto"],
)

proto_library(
    name = "pattern_detection_result",
    srcs = ["pattern_detection_result.proto"],
    deps = [":vector_proto"],
)

py_proto_library(
    name = "pattern_detection_result_py_pb2",
    deps = [":pattern_detection_result"],
)

proto_library(
    name = "vector_proto",
    srcs = ["vector.proto"],
)

py_proto_library(
    name = "vector_py_pb2",
    deps = [":vector_proto"],
)

proto_library(
    name = "charuco_pattern_proto",
    srcs = ["charuco_pattern.proto"],
)

cc_proto_library(
    name = "charuco_pattern_cc_proto",
    deps = [":charuco_pattern_proto"],
)

py_proto_library(
    name = "charuco_pattern_py_pb2",
    deps = [":charuco_pattern_proto"],
)

proto_library(
    name = "pattern_detection_config",
    srcs = ["pattern_detection_config.proto"],
    deps = [
        ":charuco_pattern_proto",
    ],
)

cc_proto_library(
    name = "pattern_detection_config_cc_proto",
    deps = ["pattern_detection_config"],
)

py_proto_library(
    name = "pattern_detection_config_py_pb2",
    deps = [":pattern_detection_config"],
)

py_proto_library(
    name = "dimensions_py_pb2",
    deps = [":dimensions_proto"],
)

py_proto_library(
    name = "hand_eye_calibration_py_pb2",
    deps = [":hand_eye_calibration"],
)

proto_library(
    name = "pose_estimator_id_proto",
    srcs = ["pose_estimator_id.proto"],
)

cc_proto_library(
    name = "pose_estimator_id_cc_proto",
    deps = [":pose_estimator_id_proto"],
)

py_proto_library(
    name = "pose_estimator_id_py_pb2",
    deps = [":pose_estimator_id_proto"],
)

proto_library(
    name = "image_processing_proto",
    srcs = ["image_processing.proto"],
)

proto_library(
    name = "point_cloud_proto",
    srcs = ["point_cloud.proto"],
    deps = [
        ":sensor_image",
        "//intrinsic/math/proto:pose_proto",
    ],
)

py_proto_library(
    name = "point_cloud_proto_py_pb2",
    deps = [":point_cloud_proto"],
)

cc_proto_library(
    name = "point_cloud_cc_proto",
    deps = [":point_cloud_proto"],
)

cc_proto_library(
    name = "image_processing_cc_proto",
    deps = [":image_processing_proto"],
)

py_proto_library(
    name = "image_processing_proto_py_pb2",
    deps = [":image_processing_proto"],
)
