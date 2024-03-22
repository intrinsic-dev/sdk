# Copyright 2023 Intrinsic Innovation LLC

# Solution building Python libraries.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
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
        ":skill_utils",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/solutions:providers",
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
        ":skills",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skill_registry_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
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
        "//intrinsic/solutions:provided",
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
        "//intrinsic/solutions:provided",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "skill_parameters",
    srcs = ["skill_parameters.py"],
    deps = ["@com_google_protobuf//:protobuf_python"],
)

py_test(
    name = "skill_parameters_test",
    srcs = ["skill_parameters_test.py"],
    srcs_version = "PY3",
    deps = [
        ":skill_parameters",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "skill_utils",
    srcs = ["skill_utils.py"],
    srcs_version = "PY3",
    deps = [
        ":skill_parameters",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/motion_planning/proto:motion_target_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:utils",
        "//intrinsic/solutions:worlds",
        "//intrinsic/util/proto:descriptors_py",
        "//intrinsic/world/proto:collision_settings_py_pb2",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/python:object_world_resources",
        requirement("grpcio"),
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "skill_utils_external_test",
    srcs = ["skill_utils_external_test.py"],
    deps = [
        ":skill_utils",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:utils",
        "//intrinsic/solutions:worlds",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "//intrinsic/world/proto:collision_settings_py_pb2",
        "//intrinsic/world/proto:object_world_service_py_pb2",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "skills",
    srcs = ["skills.py"],
    srcs_version = "PY3",
    deps = [
        ":actions",
        ":resources",
        ":skill_parameters",
        ":skill_utils",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:providers",
        "//intrinsic/solutions:utils",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "skills_test",
    srcs = ["skills_test.py"],
    data = [
        "//intrinsic/solutions/testing:test_skill_params_proto_descriptors",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":skill_utils",
        ":skills",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/executive/proto:test_message_py_pb2",
        "//intrinsic/math/proto:point_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/proto:quaternion_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/resources/proto:resource_registry_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skill_registry_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "@com_google_absl_py//absl/flags",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
    ],
)
