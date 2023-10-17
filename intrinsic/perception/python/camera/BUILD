# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = [
    "//visibility:public",
])

py_library(
    name = "_camera_utils",
    srcs = ["_camera_utils.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/perception/proto:camera_config_py_pb2",
        "//intrinsic/perception/proto:dimensions_py_pb2",
        "//intrinsic/perception/proto:distortion_params_py_pb2",
        "//intrinsic/perception/proto:intrinsic_params_py_pb2",
        requirement("numpy"),
    ],
)

py_library(
    name = "data_classes",
    srcs = ["data_classes.py"],
    srcs_version = "PY3",
    deps = [
        ":_camera_utils",
        "//intrinsic/math/python:pose3",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/perception/proto:camera_config_py_pb2",
        "//intrinsic/perception/proto:camera_params_py_pb2",
        "//intrinsic/perception/proto:capture_result_py_pb2",
        "//intrinsic/perception/proto:sensor_config_py_pb2",
        "//intrinsic/perception/proto:sensor_image_py_pb2",
        "//intrinsic/perception/python:image_utils",
        "//intrinsic/perception/service/proto:camera_server_py_pb2",
        requirement("numpy"),
    ],
)

py_library(
    name = "camera_client",
    srcs = ["camera_client.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/perception/proto:camera_config_py_pb2",
        "//intrinsic/perception/proto:camera_params_py_pb2",
        "//intrinsic/perception/proto:camera_settings_py_pb2",
        "//intrinsic/perception/proto:capture_result_py_pb2",
        "//intrinsic/perception/service/proto:camera_server_py_pb2",
        "//intrinsic/perception/service/proto:camera_server_py_pb2_grpc",
        "//intrinsic/util/grpc:connection",
        "//intrinsic/util/grpc:interceptor",
        requirement("grpcio"),
    ],
)

py_library(
    name = "cameras",
    srcs = ["cameras.py"],
    srcs_version = "PY3",
    deps = [
        ":camera_client",
        ":data_classes",
        "//intrinsic/hardware/proto:settings_py_pb2",
        "//intrinsic/math/python:pose3",
        "//intrinsic/perception/proto:camera_config_py_pb2",
        "//intrinsic/perception/proto:camera_params_py_pb2",
        "//intrinsic/skills/proto:equipment_py_pb2",
        "//intrinsic/skills/python:proto_utils",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/util/grpc:connection",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_resources",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
        "@com_google_protobuf//:protobuf_python",
        requirement("numpy"),
    ],
)
