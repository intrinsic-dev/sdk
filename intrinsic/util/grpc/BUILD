# Copyright 2023 Intrinsic Innovation LLC

"""Helper utilities for applications using grpc."""

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("//bazel:go_macros.bzl", "go_library")

package(
    default_visibility = ["//visibility:public"],
)

cc_library(
    name = "channel_interface",
    srcs = ["channel_interface.cc"],
    hdrs = ["channel_interface.h"],
    deps = [
        ":grpc",
        "@com_github_grpc_grpc//:grpc++",
    ],
)

cc_library(
    name = "channel",
    srcs = ["channel.cc"],
    hdrs = ["channel.h"],
    deps = [
        ":channel_interface",
        ":connection_params",
        ":grpc",
        "//intrinsic/util/status:status_macros",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "connection_params",
    srcs = ["connection_params.cc"],
    hdrs = ["connection_params.h"],
    deps = [
        "@com_google_absl//absl/strings:str_format",
    ],
)

py_library(
    name = "connection",
    srcs = [
        "connection.py",
    ],
    srcs_version = "PY3",
)

cc_library(
    name = "grpc",
    srcs = ["grpc.cc"],
    hdrs = ["grpc.h"],
    deps = [
        "//intrinsic/icon/release:grpc_time_support",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/thread",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//src/proto/grpc/health/v1:health_proto",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

py_library(
    name = "interceptor",
    srcs = ["interceptor.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/util:decorators",
        requirement("grpcio"),
    ],
)

py_library(
    name = "error_handling",
    srcs = ["error_handling.py"],
    srcs_version = "PY3",
    deps = [
        requirement("grpcio"),
        requirement("retrying"),
    ],
)

py_test(
    name = "error_handling_test",
    srcs = ["error_handling_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":error_handling",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

go_library(
    name = "statusutil",
    srcs = ["status_util.go"],
    deps = [
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)
