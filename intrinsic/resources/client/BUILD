# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "resource_registry_client",
    srcs = ["resource_registry_client.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/resources/proto:resource_registry_py_pb2",
        "//intrinsic/resources/proto:resource_registry_py_pb2_grpc",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
    ],
)

py_test(
    name = "resource_registry_client_test",
    srcs = ["resource_registry_client_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":resource_registry_client",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/resources/proto:resource_registry_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)
