# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(
    default_visibility = ["//visibility:public"],
)

PROTO_SRCS = [
    "ball.proto",
    "box.proto",
    "color.proto",
    "frequency.proto",
    "interval.proto",
    "matrix.proto",
    "path.proto",
    "pose.proto",
    "quaternion.proto",
    "oriented_box.proto",
    "shape.proto",
    "trajectory.proto",
    "transform.proto",
    "twist.proto",
    "vector.proto",
    "wrench.proto",
]

proto_library(
    name = "messages",
    srcs = PROTO_SRCS,
    features = ["-proto_dynamic_mode_static_link"],
    deps = [
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

py_proto_library(
    name = "messages_py_pb2",
    deps = [":messages"],
)

# ======================================================================
# Messages related to ObjectId and ObjectRef identifiers.
# ======================================================================

OBJECT_REF_PROTO_SRCS = [
    "frame_context.proto",
    "object_id.proto",
    "object_ref.proto",
]

proto_library(
    name = "object_ref_proto",
    srcs = OBJECT_REF_PROTO_SRCS,
    features = ["-proto_dynamic_mode_static_link"],
    deps = [
        ":messages",
        "@com_google_protobuf//:any_proto",
    ],
)

# ======================================================================
# Additional Proto Libraries
# ======================================================================

proto_library(
    name = "optical_chart_config_proto",
    srcs = ["optical_chart_config.proto"],
    deps = [":messages"],
)

proto_library(
    name = "calibration_proto",
    srcs = ["calibration.proto"],
    deps = [
        ":messages",
        ":object_ref_proto",
        ":stats_proto",
    ],
)

proto_library(
    name = "coordinate_frame_proto",
    srcs = ["coordinate_frame.proto"],
    deps = [
        ":array_format_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

proto_library(
    name = "fiducial_pattern_proto",
    srcs = ["fiducial_pattern.proto"],
    deps = [
        ":array_format_proto",
        ":coordinate_frame_proto",
    ],
)

proto_library(
    name = "stats_proto",
    srcs = ["stats.proto"],
)

proto_library(
    name = "array_format_proto",
    srcs = ["array_format.proto"],
    deps = ["@com_google_protobuf//:descriptor_proto"],
)

# ======================================================================
# Libraries for other languages
# ======================================================================

PROTO_LIBRARIES = [
    "array_format",
    "calibration",
    "calibration_metrics",
    "coordinate_frame",
    "fiducial_pattern",
    "metrics",
    "object_ref",
    "stats",
]
