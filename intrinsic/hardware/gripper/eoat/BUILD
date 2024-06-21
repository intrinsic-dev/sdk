# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "eoat_service_proto",
    srcs = ["eoat_service.proto"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        ":gripper_config_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

go_proto_library(
    name = "eoat_service_go_proto",
    go_deps = [
        "//intrinsic/hardware/gpio:gpio_service_go_proto",
        "//intrinsic/hardware/gripper/eoat:gripper_config_go_proto",
    ],
    deps = [":eoat_service_proto"],
)

cc_proto_library(
    name = "eoat_service_cc_proto",
    deps = [":eoat_service_proto"],
)

py_grpc_library(
    name = "eoat_service_py_pb2_grpc",
    srcs = [":eoat_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":eoat_service_py_pb2"],
)

py_proto_library(
    name = "eoat_service_py_pb2",
    deps = [":eoat_service_proto"],
)

cc_grpc_library(
    name = "eoat_service_cc_grpc_proto",
    srcs = [":eoat_service_proto"],
    grpc_only = True,
    deps = [":eoat_service_cc_proto"],
)

proto_library(
    name = "gripper_config_proto",
    srcs = ["gripper_config.proto"],
    deps = ["//intrinsic/hardware/gpio:signal_proto"],
)

go_proto_library(
    name = "gripper_config_go_proto",
    go_deps = [
        "//intrinsic/hardware/gpio:signal_go_proto",
    ],
    deps = [":gripper_config_proto"],
)

cc_proto_library(
    name = "gripper_config_cc_proto",
    deps = [":gripper_config_proto"],
)

py_library(
    name = "gripper_python_utils",
    srcs = ["gripper_python_utils.py"],
    deps = [
        ":gripper_client",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_py_pb2",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_resources",
        requirement("numpy"),
    ],
)

py_library(
    name = "gripper_client",
    srcs = ["gripper_client.py"],
    deps = [
        "eoat_service_py_pb2",
        "eoat_service_py_pb2_grpc",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_py_pb2",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_py_pb2_grpc",
        "//intrinsic/icon/python:icon",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/util/grpc:connection",
        "//intrinsic/util/grpc:interceptor",
        requirement("grpcio"),
    ],
)
