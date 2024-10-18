# Copyright 2023 Intrinsic Innovation LLC

# Solution building Python libraries.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load(
    "//intrinsic/util/proto/build_defs:descriptor_set.bzl",
    "proto_source_code_info_transitive_descriptor_set",
)

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
        "//intrinsic/solutions/testing:compare",
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
    deps = [
        "//intrinsic/skills/proto:skills_py_pb2",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "skill_parameters_test",
    srcs = ["skill_parameters_test.py"],
    data = [
        "//intrinsic/solutions/testing:test_skill_params_proto_descriptors",
    ],
    srcs_version = "PY3",
    deps = [
        ":skill_parameters",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions/testing:skill_test_utils",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
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
        "//intrinsic/perception/proto:pose_estimator_id_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:pose_estimation",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:utils",
        "//intrinsic/solutions:worlds",
        "//intrinsic/util/proto:descriptors_py",
        "//intrinsic/world/proto:collision_settings_py_pb2",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/proto:robot_payload_py_pb2",
        "//intrinsic/world/python:object_world_resources",
        "//intrinsic/world/robot_payload/python:robot_payload",
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
    name = "skill_generation",
    srcs = ["skill_generation.py"],
    srcs_version = "PY3",
    deps = [
        ":actions",
        ":skill_utils",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:utils",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "skill_providing",
    srcs = ["skill_providing.py"],
    srcs_version = "PY3",
    deps = [
        ":resources",
        ":skill_generation",
        ":skill_utils",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:providers",
    ],
)

py_test(
    name = "skill_providing_test",
    srcs = ["skill_providing_test.py"],
    data = [
        "//intrinsic/solutions/testing:test_skill_params_proto_descriptors",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":skill_generation",
        ":skill_providing",
        ":skill_utils",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/executive/proto:test_message_py_pb2",
        "//intrinsic/math/proto:point_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/proto:quaternion_py_pb2",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skill_registry_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:blackboard_value",
        "//intrinsic/solutions:cel",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/solutions/testing:skill_test_utils",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "stubs",
    srcs = ["stubs.py"],
    deps = [
        ":skill_generation",
        ":skill_utils",
        "//intrinsic/math/python:data_types",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:providers",
        "@ai_intrinsic_sdks_pip_deps//black",
        "@ai_intrinsic_sdks_pip_deps//typing_extensions",
    ],
)

py_library(
    name = "products",
    srcs = ["products.py"],
    deps = [
        "//intrinsic/scene/product/client:product_client",
        "//intrinsic/scene/proto:scene_object_py_pb2",
        "//intrinsic/solutions:provided",
        "//intrinsic/solutions:providers",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "products_test",
    srcs = ["products_test.py"],
    deps = [
        ":products",
        "//intrinsic/scene/product/proto:product_py_pb2",
        "//intrinsic/scene/proto:scene_object_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

proto_library(
    name = "stubs_test_proto",
    srcs = ["stubs_test.proto"],
    deps = [
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

py_proto_library(
    name = "stubs_test_py_pb2",
    deps = [":stubs_test_proto"],
)

proto_source_code_info_transitive_descriptor_set(
    name = "stubs_test_proto_descriptors",
    deps = [":stubs_test_proto"],
)

py_test(
    name = "stubs_test",
    srcs = ["stubs_test.py"],
    data = [
        ":stubs_test_proto_descriptors",
    ],
    srcs_version = "PY3",
    deps = [
        ":skill_providing",
        ":stubs",
        ":stubs_test_py_pb2",
        "//intrinsic/solutions/testing:skill_test_utils",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)
