# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("//bazel:go_macros.bzl", "go_proto_library")

package(
    default_visibility = [
        "//visibility:public",
    ],
)

proto_library(
    name = "types_proto",
    srcs = ["types.proto"],
    deps = [
        ":generic_part_config_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:descriptor_proto",
    ],
)

cc_proto_library(
    name = "types_cc_proto",
    deps = [":types_proto"],
)

py_proto_library(
    name = "types_py_pb2",
    deps = [":types_proto"],
)

proto_library(
    name = "service_proto",
    srcs = ["service.proto"],
    deps = [
        ":joint_space_proto",
        ":part_status_proto",
        ":safety_status_proto",
        ":streaming_output_proto",
        ":types_proto",
        "//intrinsic/logging/proto:context_proto",
        "@com_google_googleapis//google/rpc:status_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:duration_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "service_cc_proto",
    deps = [":service_proto"],
)

proto_library(
    name = "generic_part_config_proto",
    srcs = ["generic_part_config.proto"],
    deps = [
        ":cart_space_proto",
        "//intrinsic/kinematics/proto:skeleton_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

cc_proto_library(
    name = "generic_part_config_cc_proto",
    deps = [":generic_part_config_proto"],
)

py_proto_library(
    name = "generic_part_config_py_pb2",
    deps = [":generic_part_config_proto"],
)

proto_library(
    name = "part_status_proto",
    srcs = ["part_status.proto"],
    deps = [
        ":cart_space_proto",
        ":io_block_proto",
        ":safety_status_proto",
        "//intrinsic/math/proto:quaternion_proto",
        "//intrinsic/math/proto:vector3_proto",
    ],
)

cc_proto_library(
    name = "part_status_cc_proto",
    deps = [":part_status_proto"],
)

py_proto_library(
    name = "service_py_pb2",
    deps = [":service_proto"],
)

py_proto_library(
    name = "part_status_py_pb2",
    deps = [":part_status_proto"],
)

cc_grpc_library(
    name = "service_cc_grpc_proto",
    srcs = [":service_proto"],
    grpc_only = True,
    deps = [":service_cc_proto"],
)

py_grpc_library(
    name = "service_py_pb2_grpc",
    srcs = [":service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":service_py_pb2"],
)

proto_library(
    name = "streaming_output_proto",
    srcs = ["streaming_output.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "streaming_output_cc_proto",
    deps = [":streaming_output_proto"],
)

py_proto_library(
    name = "streaming_output_py_pb2",
    deps = [":streaming_output_proto"],
)

cc_library(
    name = "eigen_conversion",
    srcs = ["eigen_conversion.cc"],
    hdrs = ["eigen_conversion.h"],
    deps = [
        ":cart_space_cc_proto",
        ":joint_space_cc_proto",
        ":matrix_cc_proto",
        "//intrinsic/eigenmath",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

proto_library(
    name = "matrix_proto",
    srcs = ["matrix.proto"],
)

cc_proto_library(
    name = "matrix_cc_proto",
    deps = [":matrix_proto"],
)

py_proto_library(
    name = "matrix_py_pb2",
    deps = [":matrix_proto"],
)

proto_library(
    name = "cart_space_proto",
    srcs = ["cart_space.proto"],
)

cc_proto_library(
    name = "cart_space_cc_proto",
    deps = [":cart_space_proto"],
)

py_proto_library(
    name = "cart_space_py_pb2",
    deps = [":cart_space_proto"],
)

go_proto_library(
    name = "cart_space_go_proto",
    deps = [":cart_space_proto"],
)

cc_library(
    name = "cart_space_conversion",
    srcs = ["cart_space_conversion.cc"],
    hdrs = ["cart_space_conversion.h"],
    deps = [
        ":cart_space_cc_proto",
        ":eigen_conversion",
        "//intrinsic/eigenmath",
        "//intrinsic/kinematics/types:cartesian_limits",
        "//intrinsic/math:pose3",
        "//intrinsic/math:twist",
        "//intrinsic/util/status:status_builder",
        "//intrinsic/util/status:status_macros",
        "@com_gitlab_libeigen_eigen//:eigen",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "concatenate_trajectory_protos",
    srcs = ["concatenate_trajectory_protos.cc"],
    hdrs = ["concatenate_trajectory_protos.h"],
    deps = [
        ":joint_space_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_protobuf//:protobuf",
    ],
)

proto_library(
    name = "joint_space_proto",
    srcs = ["joint_space.proto"],
    deps = [
        "//intrinsic/kinematics/types:dynamic_limits_check_mode_proto",
        "//intrinsic/skills/proto:skill_parameter_metadata_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

cc_proto_library(
    name = "joint_space_cc_proto",
    deps = [":joint_space_proto"],
)

py_proto_library(
    name = "joint_space_py_pb2",
    deps = [":joint_space_proto"],
)

proto_library(
    name = "ik_options_proto",
    srcs = ["ik_options.proto"],
)

cc_proto_library(
    name = "ik_options_cc_proto",
    deps = [":ik_options_proto"],
)

py_proto_library(
    name = "ik_options_py_pb2",
    deps = [":ik_options_proto"],
)

proto_library(
    name = "io_block_proto",
    srcs = ["io_block.proto"],
)

py_proto_library(
    name = "io_block_py_pb2",
    deps = [":io_block_proto"],
)

cc_proto_library(
    name = "io_block_cc_proto",
    deps = [":io_block_proto"],
)

py_library(
    name = "matrix_conversions",
    srcs = ["matrix_conversions.py"],
    srcs_version = "PY3",
    deps = [
        ":matrix_py_pb2",
        requirement("numpy"),
    ],
)

py_test(
    name = "matrix_conversions_test",
    srcs = ["matrix_conversions_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":matrix_conversions",
        ":matrix_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        requirement("numpy"),
    ],
)

proto_library(
    name = "linear_joint_acceleration_filter_config_proto",
    srcs = [
        "linear_joint_acceleration_filter_config.proto",
    ],
)

cc_proto_library(
    name = "linear_joint_acceleration_filter_config_cc_proto",
    deps = [":linear_joint_acceleration_filter_config_proto"],
)

go_proto_library(
    name = "linear_joint_acceleration_filter_config_go_proto",
    deps = [":linear_joint_acceleration_filter_config_proto"],
)

proto_library(
    name = "blended_cartesian_move_proto",
    srcs = ["blended_cartesian_move.proto"],
    deps = [
        ":cart_space_proto",
        ":joint_space_proto",
        "//intrinsic/kinematics/types:joint_limits_proto",
        "//intrinsic/math/proto:pose_proto",
    ],
)

proto_library(
    name = "joint_position_pid_torque_controller_config_proto",
    srcs = [
        "joint_position_pid_torque_controller_config.proto",
    ],
)

go_proto_library(
    name = "joint_position_pid_torque_controller_config_go_proto",
    deps = [":joint_position_pid_torque_controller_config_proto"],
)

proto_library(
    name = "safety_status_proto",
    srcs = ["safety_status.proto"],
)

cc_proto_library(
    name = "safety_status_cc_proto",
    deps = [":safety_status_proto"],
)

py_proto_library(
    name = "safety_status_py_pb2",
    deps = [":safety_status_proto"],
)

cc_proto_library(
    name = "blended_cartesian_move_cc_proto",
    deps = [":blended_cartesian_move_proto"],
)

py_proto_library(
    name = "blended_cartesian_move_py_pb2",
    deps = [":blended_cartesian_move_proto"],
)

proto_library(
    name = "icon_protos",
    deps = [
        ":blended_cartesian_move_proto",
        ":cart_space_proto",
        ":generic_part_config_proto",
        ":ik_options_proto",
        ":io_block_proto",
        ":joint_space_proto",
        ":matrix_proto",
        ":part_status_proto",
        ":safety_status_proto",
        ":service_proto",
        ":streaming_output_proto",
        ":types_proto",
    ],
)
