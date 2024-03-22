# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

exports_files(srcs = [
    "robot_payload.py",
    "robot_payload_test.py",
])

py_library(
    name = "robot_payload",
    srcs = ["robot_payload.py"],
    deps = [
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/world/proto:robot_payload_py_pb2",
        requirement("numpy"),
    ],
)

py_test(
    name = "robot_payload_test",
    srcs = ["robot_payload_test.py"],
    deps = [
        ":robot_payload",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/world/proto:robot_payload_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)
