# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

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
        "//intrinsic/world/python:object_world_client",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)
