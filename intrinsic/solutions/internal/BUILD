# Copyright 2023 Intrinsic Innovation LLC

# Solution building Python libraries.

load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = [
    "//intrinsic/solutions:__subpackages__",
])

py_library(
    name = "actions",
    srcs = ["actions.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/skills/proto:skills_py_pb2",
    ],
)

py_library(
    name = "behavior_call",
    srcs = ["behavior_call.py"],
    srcs_version = "PY3",
    deps = [
        ":actions",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/solutions:providers",
        "//intrinsic/solutions:skill_utils",
        "//intrinsic/solutions:utils",
    ],
)

py_test(
    name = "behavior_call_test",
    srcs = ["behavior_call_test.py"],
    data = [
        "//intrinsic/solutions/testing:test_skill_params_proto_descriptors",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":actions",
        ":behavior_call",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skill_registry_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:skills",
        "//intrinsic/solutions:utils",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "@com_google_absl_py//absl/flags",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "resources",
    srcs = ["resources.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/solutions:providers",
    ],
)

py_test(
    name = "resources_test",
    srcs = ["resources_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":resources",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/solutions:providers",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)
