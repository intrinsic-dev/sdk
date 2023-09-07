# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "proto_conversion",
    srcs = ["proto_conversion.py"],
    srcs_version = "PY3",
    deps = [
        ":data_types",
        "//intrinsic/math/proto:array_py_pb2",
        "//intrinsic/math/proto:point_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/proto:quaternion_py_pb2",
        "//intrinsic/math/proto:vector3_py_pb2",
        requirement("numpy"),
    ],
)

py_test(
    name = "proto_conversion_test",
    srcs = ["proto_conversion_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":data_types",
        ":proto_conversion",
        "//intrinsic/icon/proto:cart_space_py_pb2",
        "//intrinsic/math/proto:array_py_pb2",
        "//intrinsic/math/proto:point_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/proto:quaternion_py_pb2",
        "//intrinsic/math/proto:vector3_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "data_types",
    srcs = ["data_types.py"],
    srcs_version = "PY3",
    deps = [
        ":math_types",
        ":pose3",
        ":quaternion",
        ":rotation3",
        "//intrinsic/icon/proto:cart_space_py_pb2",
        "//intrinsic/robotics/pymath:vector_util",
        requirement("numpy"),
    ],
)

py_test(
    name = "data_types_test",
    size = "small",
    srcs = ["data_types_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":data_types",
        "//intrinsic/icon/proto:cart_space_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        requirement("numpy"),
    ],
)

py_library(
    name = "math_test",
    testonly = 1,
    srcs = ["math_test.py"],
    deps = [
        ":math_types",
        ":pose3",
        ":quaternion",
        ":rotation3",
        "//intrinsic/robotics/pymath:vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        requirement("numpy"),
    ],
)

py_test(
    name = "math_test_test",
    size = "small",
    srcs = [
        "math_test_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":math_types",
        ":pose3",
        ":rotation3",
        "//intrinsic/robotics/pymath:vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "math_types",
    srcs = ["math_types.py"],
    deps = [requirement("numpy")],
)

py_test(
    name = "math_types_test",
    size = "small",
    srcs = [
        "math_types_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":math_types",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "pose3",
    srcs = [
        "pose3.py",
    ],
    deps = [
        ":math_types",
        ":quaternion",
        ":rotation3",
        "//intrinsic/robotics/pymath:vector_util",
        requirement("numpy"),
    ],
)

py_test(
    name = "pose3_test",
    size = "medium",
    srcs = [
        "pose3_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":pose3",
        ":quaternion",
        ":rotation3",
        "//intrinsic/robotics/pymath:vector_util",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "rotation3",
    srcs = [
        "rotation3.py",
    ],
    deps = [
        ":math_types",
        ":quaternion",
        "//intrinsic/robotics/pymath:vector_util",
        requirement("numpy"),
    ],
)

py_test(
    name = "rotation3_test",
    size = "small",
    timeout = "moderate",
    srcs = [
        "rotation3_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":math_types",
        ":quaternion",
        ":rotation3",
        "//intrinsic/robotics/pymath:vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "quaternion",
    srcs = [
        "quaternion.py",
    ],
    deps = [
        ":math_types",
        "//intrinsic/robotics/pymath:vector_util",
        requirement("numpy"),
    ],
)

py_test(
    name = "quaternion_test",
    size = "small",
    srcs = [
        "quaternion_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":quaternion",
        "//intrinsic/robotics/pymath:vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)
