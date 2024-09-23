# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

# This package contains the code execution service.

py_library(
    name = "code_execution",
    srcs = ["code_execution.py"],
    deps = [
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/skills/internal:basic_compute_context_impl_py",
        "//intrinsic/skills/python:basic_compute_context",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        "//intrinsic/world/python:object_world_client",
        requirement("grpcio"),
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "code_execution_test",
    srcs = ["code_execution_test.py"],
    deps = [
        ":code_execution",
        "//intrinsic/math/proto:point_py_pb2",
        "//intrinsic/skills/python:basic_compute_context",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/python:object_world_client",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_package(
    name = "code_execution_py_packages",
    packages = [
        "intrinsic",
    ],
    deps = [
        "//intrinsic/executive/code:code_execution",
    ],
)

py_wheel(
    name = "code_execution_wheel",
    distribution = "code-execution",
    requires = [
        "googleapis-common-protos",
        "grpcio",
        "retrying",
    ],
    version = "0.0.1",
    deps = [":code_execution_py_packages"],
)
