# Copyright 2023 Intrinsic Innovation LLC

# Solution building Python libraries.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

package(default_visibility = [
    "//visibility:public",
])

py_library(
    name = "behavior_tree",
    srcs = ["behavior_tree.py"],
    srcs_version = "PY3",
    deps = [
        ":blackboard_value",
        ":cel",
        ":errors",
        ":ipython",
        ":proto_building",
        ":utils",
        "//intrinsic/executive/proto:any_list_py_pb2",
        "//intrinsic/executive/proto:any_with_assignments_py_pb2",
        "//intrinsic/executive/proto:behavior_call_py_pb2",
        "//intrinsic/executive/proto:behavior_tree_py_pb2",
        "//intrinsic/executive/proto:world_query_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions/internal:actions",
        "//intrinsic/solutions/internal:skill_generation",
        "//intrinsic/solutions/internal:skill_utils",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_protobuf//:protobuf_python",
        requirement("graphviz"),
    ],
)

py_test(
    name = "behavior_tree_test",
    srcs = ["behavior_tree_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":behavior_tree",
        ":blackboard_value",
        ":errors",
        "//intrinsic/executive/proto:any_with_assignments_py_pb2",
        "//intrinsic/executive/proto:behavior_tree_py_pb2",
        "//intrinsic/executive/proto:test_message_py_pb2",
        "//intrinsic/executive/proto:world_query_py_pb2",
        "//intrinsic/solutions/internal:behavior_call",
        "//intrinsic/solutions/testing:compare",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/proto:object_world_service_py_pb2",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "blackboard_value",
    srcs = ["blackboard_value.py"],
    srcs_version = "PY3",
    deps = [
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "camera_utils",
    srcs = ["camera_utils.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/perception/proto:frame_py_pb2",
        "//intrinsic/perception/proto:image_buffer_py_pb2",
        "//intrinsic/perception/python:image_utils",
        requirement("matplotlib"),
    ],
)

py_test(
    name = "camera_utils_external_test",
    srcs = ["camera_utils_external_test.py"],
    deps = [
        ":camera_utils",
        "//intrinsic/perception/proto:frame_py_pb2",
        "//intrinsic/perception/proto:image_buffer_py_pb2",
        "//intrinsic/solutions/testing:compare",
        "@com_google_absl_py//absl/testing:absltest",
        requirement("numpy"),
    ],
)

py_library(
    name = "cel",
    srcs = ["cel.py"],
)

py_library(
    name = "deployments",
    srcs = ["deployments.py"],
    srcs_version = "PY3",
    deps = [
        ":auth",
        ":dialerutil",
        ":error_processing",
        ":errors",
        ":execution",
        ":ipython",
        ":pbt_registration",
        ":pose_estimation",
        ":proto_building",
        ":providers",
        ":simulation",
        ":userconfig",
        ":worlds",
        "//intrinsic/frontend/cloud/api:solutiondiscovery_api_py_pb2",
        "//intrinsic/frontend/cloud/api:solutiondiscovery_api_py_pb2_grpc",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2_grpc",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/solutions/internal:resources",
        "//intrinsic/solutions/internal:skill_providing",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "deployments_test",
    srcs = ["deployments_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":auth",
        ":deployments",
        ":dialerutil",
        ":error_processing",
        ":errors",
        ":execution",
        ":simulation",
        ":userconfig",
        ":worlds",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2",
        "//intrinsic/skills/client:skill_registry_client",
        "//intrinsic/skills/proto:skill_registry_py_pb2",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "userconfig",
    srcs = ["userconfig.py"],
    srcs_version = "PY3",
)

py_test(
    name = "userconfig_test",
    srcs = ["userconfig_test.py"],
    deps = [
        ":userconfig",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "errors",
    srcs = ["errors.py"],
    srcs_version = "PY3",
    deps = [
        requirement("retrying"),
    ],
)

py_library(
    name = "error_processing",
    srcs = ["error_processing.py"],
    srcs_version = "PY3",
    deps = [
        ":camera_utils",
        ":errors",
        ":ipython",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2_grpc",
        "//intrinsic/logging/errors/proto:error_report_py_pb2",
        "//intrinsic/perception/proto:frame_py_pb2",
        requirement("grpcio"),  # buildcleaner: keep
        "@com_google_googleapis//google/longrunning:operations_py_proto",
        "@com_google_googleapis//google/rpc:code_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "error_processing_test",
    srcs = ["error_processing_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":error_processing",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2",
        "//intrinsic/logging/errors/proto:error_report_py_pb2",
        "//intrinsic/solutions/testing:compare",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_googleapis//google/longrunning:operations_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "execution",
    srcs = ["execution.py"],
    srcs_version = "PY3",
    deps = [
        ":behavior_tree",
        ":blackboard_value",
        ":error_processing",
        ":errors",
        ":ipython",
        ":simulation",
        ":utils",
        "//intrinsic/executive/proto:behavior_tree_py_pb2",
        "//intrinsic/executive/proto:blackboard_service_py_pb2",
        "//intrinsic/executive/proto:blackboard_service_py_pb2_grpc",
        "//intrinsic/executive/proto:executive_execution_mode_py_pb2",
        "//intrinsic/executive/proto:executive_service_py_pb2",
        "//intrinsic/executive/proto:executive_service_py_pb2_grpc",
        "//intrinsic/executive/proto:run_metadata_py_pb2",
        "//intrinsic/solutions/internal:actions",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
        "@com_google_googleapis//google/longrunning:operations_py_proto",
    ],
)

py_test(
    name = "execution_test",
    srcs = ["execution_test.py"],
    data = [
        "//intrinsic/solutions/testing:test_skill_params_proto_descriptors",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":behavior_tree",
        ":blackboard_value",
        ":error_processing",
        ":errors",
        ":execution",
        ":simulation",
        "//intrinsic/executive/proto:behavior_tree_py_pb2",
        "//intrinsic/executive/proto:blackboard_service_py_pb2",
        "//intrinsic/executive/proto:blackboard_service_py_pb2_grpc",
        "//intrinsic/executive/proto:executive_execution_mode_py_pb2",
        "//intrinsic/executive/proto:executive_service_py_pb2",
        "//intrinsic/executive/proto:executive_service_py_pb2_grpc",
        "//intrinsic/executive/proto:run_metadata_py_pb2",
        "//intrinsic/logging/errors/proto:error_report_py_pb2",
        "//intrinsic/solutions/internal:behavior_call",
        "//intrinsic/solutions/testing:test_skill_params_py_pb2",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
        "@com_google_googleapis//google/longrunning:operations_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "ipython",
    srcs = ["ipython.py"],
    srcs_version = "PY3",
)

py_test(
    name = "ipython_test",
    srcs = ["ipython_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":ipython",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

# Pseudo binary target with all dependendies of the solutions lib.
py_binary(
    name = "main",
    srcs = ["main.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":solutions_lib",
    ],
)

# Collection of all "public" modules for packaging.
py_library(
    name = "solutions_lib",
    srcs_version = "PY3",
    deps = [
        ":blackboard_value",
        ":cel",
        ":deployments",
        ":errors",
        ":execution",
        ":perception",
        ":pose_estimation",
        ":ppr",
        ":providers",
        ":simulation",
        ":worlds",
    ],
)

py_library(
    name = "perception",
    srcs = ["perception.py"],
    srcs_version = "PY3",
    deps = [
        ":camera_utils",
        ":deployments",
        ":execution",
        "//intrinsic/perception/proto:camera_config_py_pb2",
        "//intrinsic/perception/python/camera:data_classes",
        "//intrinsic/perception/service/proto:camera_server_py_pb2",
        "//intrinsic/perception/service/proto:camera_server_py_pb2_grpc",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/util/grpc:connection",
        "//intrinsic/util/grpc:error_handling",
        "//intrinsic/util/grpc:interceptor",
        requirement("grpcio"),
        requirement("matplotlib"),
        requirement("numpy"),
    ],
)

py_test(
    name = "perception_external_test",
    srcs = ["perception_external_test.py"],
    deps = [
        ":perception",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "pose_estimation",
    srcs = ["pose_estimation.py"],
    srcs_version = "PY3",
    deps = [
        ":ipython",
        "//intrinsic/perception/proto:pose_estimator_id_py_pb2",
        "//intrinsic/resources/client:resource_registry_client",
        "//intrinsic/util/grpc:error_handling",
    ],
)

py_test(
    name = "pose_estimation_test",
    srcs = ["pose_estimation_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":pose_estimation",
        "//intrinsic/resources/proto:resource_registry_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "ppr",
    srcs = ["ppr.py"],
    deps = ["//intrinsic/config/proto:ppr_refs_py_pb2"],
)

py_library(
    name = "proto_building",
    srcs = ["proto_building.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/executive/proto:proto_builder_py_pb2",
        "//intrinsic/executive/proto:proto_builder_py_pb2_grpc",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "pbt_registration",
    srcs = ["pbt_registration.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/executive/proto:behavior_tree_py_pb2",
        "//intrinsic/skills/proto:behavior_tree_registry_py_pb2",
        "//intrinsic/skills/proto:behavior_tree_registry_py_pb2_grpc",
        "//intrinsic/skills/proto:skill_registry_config_py_pb2",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
    ],
)

py_library(
    name = "simulation",
    srcs = ["simulation.py"],
    srcs_version = "PY3",
    deps = [
        ":errors",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/simulation/service/proto:simulation_service_py_pb2",
        "//intrinsic/simulation/service/proto:simulation_service_py_pb2_grpc",
        "//intrinsic/util/grpc:error_handling",
        "//intrinsic/world/proto:object_world_service_py_pb2",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        "//intrinsic/world/python:object_world_resources",
        requirement("grpcio"),
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "simulation_external_test",
    srcs = ["simulation_external_test.py"],
    deps = [
        ":simulation",
        "//intrinsic/simulation/service/proto:simulation_service_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "provided",
    srcs = ["provided.py"],
    srcs_version = "PY3",
    deps = [
        ":blackboard_value",
        ":utils",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions/internal:actions",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "providers",
    srcs = ["providers.py"],
    srcs_version = "PY3",
    deps = [
        ":provided",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
    ],
)

py_library(
    name = "auth",
    srcs = ["auth.py"],
    srcs_version = "PY3",
    deps = [
        ":userconfig",
    ],
)

py_library(
    name = "dialerutil",
    srcs = ["dialerutil.py"],
    srcs_version = "PY3",
    deps = [
        ":auth",
        requirement("grpcio"),
    ],
)

py_test(
    name = "auth_test",
    srcs = ["auth_test.py"],
    deps = [
        ":auth",
        ":userconfig",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_test(
    name = "dialerutil_test",
    srcs = ["dialerutil_test.py"],
    deps = [
        ":auth",
        ":dialerutil",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "utils",
    srcs = ["utils.py"],
    srcs_version = "PY3",
    deps = [":errors"],
)

py_test(
    name = "utils_test",
    srcs = ["utils_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":utils",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_library(
    name = "worlds",
    srcs = ["worlds.py"],
    srcs_version = "PY3",
    deps = [
        ":ppr",
        ":utils",
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/math/python:data_types",
        "//intrinsic/math/python:proto_conversion",
        "//intrinsic/motion_planning/proto:motion_target_py_pb2",
        "//intrinsic/world/proto:collision_settings_py_pb2",
        "//intrinsic/world/proto:object_world_refs_py_pb2",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_ids",
        "//intrinsic/world/python:object_world_resources",
        requirement("grpcio"),
    ],
)

py_test(
    name = "worlds_external_test",
    srcs = ["worlds_external_test.py"],
    deps = [
        ":worlds",
        "//intrinsic/world/proto:object_world_service_py_pb2",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_package(
    name = "solutions_py_package",
    packages = [
        "intrinsic",
    ],
    deps = [
        ":solutions_lib",
    ],
)

py_wheel(
    name = "solutions_wheel",
    distribution = "solutions",
    requires = [
        "black",
        "googleapis-common-protos",
        "graphviz",
        "grpcio",
        "matplotlib",
        "numpy",
        "retrying",
        "typing-extensions",
    ],
    version = "0.0.1",
    deps = [":solutions_py_package"],
)
