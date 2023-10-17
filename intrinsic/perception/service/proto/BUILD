# Copyright 2023 Intrinsic Innovation LLC

# This package contains internal proto definition required for implementing the
# perception services.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "camera_server_proto",
    srcs = ["camera_server.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/perception/proto:camera_config",
        "//intrinsic/perception/proto:camera_identifier_proto",
        "//intrinsic/perception/proto:camera_params_proto",
        "//intrinsic/perception/proto:camera_settings_proto",
        "//intrinsic/perception/proto:capture_result_proto",
        "//intrinsic/perception/proto:dimensions_proto",
        "//intrinsic/perception/proto:distortion_params_proto",
        "//intrinsic/perception/proto:frame_post_processing_proto",
        "//intrinsic/perception/proto:frame_proto",
        "//intrinsic/perception/proto:image_buffer_proto",
        "//intrinsic/perception/proto:intrinsic_params_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

py_proto_library(
    name = "camera_server_py_pb2",
    deps = [":camera_server_proto"],
)

py_grpc_library(
    name = "camera_server_py_pb2_grpc",
    srcs = [":camera_server_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":camera_server_py_pb2"],
)

cc_proto_library(
    name = "camera_server_cc_proto",
    deps = [":camera_server_proto"],
)

cc_grpc_library(
    name = "camera_server_cc_grpc",
    srcs = [":camera_server_proto"],
    grpc_only = True,
    deps = [":camera_server_cc_proto"],
)
