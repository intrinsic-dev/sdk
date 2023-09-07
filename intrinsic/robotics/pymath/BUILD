# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Useful math libraries for robotics.  Python version.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(
    default_visibility = ["//visibility:public"],
)

# ------------------------------------------------------------------------------
# Python Libraries and Tests
# ------------------------------------------------------------------------------

py_library(
    name = "box",
    srcs = [
        "box.py",
    ],
    deps = [
        ":interval",
        ":math_types",
        ":proto_util",
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_test(
    name = "box_test",
    size = "small",
    srcs = [
        "box_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":box",
        ":interval",
        ":math_test",
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        requirement("numpy"),
    ],
)

py_library(
    name = "coordinate_system",
    srcs = [
        "coordinate_system.py",
    ],
    deps = [
        ":math_types",
        ":quaternion",
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        requirement("numpy"),
    ],
)

py_test(
    name = "coordinate_system_test",
    size = "medium",
    srcs = [
        "coordinate_system_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":coordinate_system",
        ":math_test",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)

py_library(
    name = "interval",
    srcs = [
        "interval.py",
    ],
    deps = [
        ":math_types",
        ":vector_util",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_test(
    name = "interval_test",
    size = "small",
    srcs = [
        "interval_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":interval",
        ":math_test",
        ":math_types",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_library(
    name = "math_test",
    testonly = 1,
    srcs = ["math_test.py"],
    deps = [
        ":box",
        ":interval",
        ":math_types",
        ":pose3",
        ":quaternion",
        ":rotation3",
        ":vector_util",
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
        ":interval",
        ":math_test",
        ":math_types",
        ":pose3",
        ":rotation3",
        ":vector_util",
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
        ":box",
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
        ":rotation3",
        ":vector_util",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_library(
    name = "quaternion",
    srcs = [
        "quaternion.py",
    ],
    deps = [
        ":vector_util",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
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
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_library(
    name = "rotation3",
    srcs = [
        "rotation3.py",
    ],
    deps = [
        ":quaternion",
        ":vector_util",
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
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_library(
    name = "proto_util",
    srcs = [
        "proto_util.py",
    ],
    deps = [
        ":math_types",
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        requirement("numpy"),
        "//intrinsic/robotics/messages:messages_py_pb2",
    ],
)

py_library(
    name = "vector_util",
    srcs = [
        "vector_util.py",
    ],
    deps = [
        ":math_types",
        requirement("numpy"),
    ],
)

py_test(
    name = "vector_util_test",
    size = "small",
    srcs = [
        "vector_util_test.py",
    ],
    python_version = "PY3",
    deps = [
        ":math_test",
        ":vector_util",
        "@com_google_absl_py//absl/logging",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        requirement("numpy"),
    ],
)
