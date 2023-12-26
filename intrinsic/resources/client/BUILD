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

cc_library(
    name = "resource_registry_client_interface",
    hdrs = ["resource_registry_client_interface.h"],
    deps = [
        "//intrinsic/resources/proto:resource_registry_cc_proto",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
    ],
)

cc_library(
    name = "resource_registry_client_cc",
    srcs = ["resource_registry_client.cc"],
    hdrs = ["resource_registry_client.h"],
    deps = [
        ":resource_registry_client_interface",
        "//intrinsic/resources/proto:resource_registry_cc_grpc",
        "//intrinsic/resources/proto:resource_registry_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/status:status_macros",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/time",
    ],
)
