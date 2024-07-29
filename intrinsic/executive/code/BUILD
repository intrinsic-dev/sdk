# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_library", "py_test")

# This package contains the code execution service.

py_library(
    name = "code_execution",
    srcs = ["code_execution.py"],
    deps = ["@com_google_protobuf//:protobuf_python"],
)

py_test(
    name = "code_execution_test",
    srcs = ["code_execution_test.py"],
    deps = [
        ":code_execution",
        "//intrinsic/math/proto:point_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)
