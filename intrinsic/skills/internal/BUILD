# Copyright 2023 Intrinsic Innovation LLC

# This directory should contain code that is used internally to our platform.
# Some files may still be exported as part of the Skills SDK, but they should
# not needed to be included directly when authoring a Skill.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("//bazel:python_oci_image.bzl", "python_oci_image")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(default_visibility = ["//intrinsic/skills:__subpackages__"])

exports_files(
    [
        "module_skill_service_main.py",
        "templates/skill_image_builder.yaml",
    ],
    visibility = [
        "//visibility:public",
    ],
)

cc_library(
    name = "default_parameters",
    srcs = ["default_parameters.cc"],
    hdrs = ["default_parameters.h"],
    deps = [
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/proto:merge",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "default_parameters_py",
    srcs = ["default_parameters.py"],
    data = [
        ":error_bindings.so",
        "@pybind11_abseil//pybind11_abseil:status.so",
    ],
    srcs_version = "PY3",
    deps = ["@com_google_protobuf//:protobuf_python"],
)

cc_library(
    name = "equipment_utilities",
    srcs = ["equipment_utilities.cc"],
    hdrs = ["equipment_utilities.h"],
    deps = [
        "//intrinsic/resources/proto:resource_handle_cc_proto",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:footprint_cc_proto",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "error_utils",
    srcs = ["error_utils.cc"],
    hdrs = ["error_utils.h"],
    deps = [
        "//intrinsic/skills/proto:error_cc_proto",
        "//intrinsic/util/proto:type_url",
        "//intrinsic/util/status:status_conversion_rpc",
        "@com_github_grpc_grpc//:grpc++_public_hdrs",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings:cord",
        "@com_google_googleapis//google/rpc:status_cc_proto",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "error_utils_py",
    srcs = ["error_utils.py"],
    data = ["@pybind11_abseil//pybind11_abseil:status.so"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/skills/proto:error_py_pb2",
        requirement("grpcio"),
        "@com_google_googleapis//google/rpc:status_py_proto",
    ],
)

pybind_extension(
    name = "error_bindings",
    srcs = ["error_bindings.cc"],
    deps = [
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@pybind11_abseil//pybind11_abseil:status_casters",
    ],
)

py_library(
    name = "module_utils",
    srcs = ["module_utils.py"],
    srcs_version = "PY3",
)

cc_library(
    name = "get_footprint_context_impl",
    srcs = ["get_footprint_context_impl.cc"],
    hdrs = ["get_footprint_context_impl.h"],
    deps = [
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/resources/proto:resource_handle_cc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:footprint_cc_proto",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/objects:frame",
        "//intrinsic/world/objects:kinematic_object",
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/objects:object_world_ids",
        "//intrinsic/world/objects:world_object",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

py_library(
    name = "get_footprint_context_impl_py",
    srcs = ["get_footprint_context_impl.py"],
    deps = [
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/python:get_footprint_context",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_ids",
        "//intrinsic/world/python:object_world_resources",
    ],
)

cc_library(
    name = "execute_context_impl",
    hdrs = ["execute_context_impl.h"],
    deps = [
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/world/objects:object_world_client",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

py_library(
    name = "execute_context_impl_py",
    srcs = ["execute_context_impl.py"],
    deps = [
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/python:execute_context",
        "//intrinsic/skills/python:skill_canceller",
        "//intrinsic/skills/python:skill_logging_context",
        "//intrinsic/world/python:object_world_client",
    ],
)

cc_library(
    name = "execute_context_view",
    hdrs = ["execute_context_view.h"],
    deps = [
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/world/objects:object_world_client",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "preview_context_impl",
    srcs = ["preview_context_impl.cc"],
    hdrs = ["preview_context_impl.h"],
    deps = [
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/resources/proto:resource_handle_cc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:preview_context",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:prediction_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/objects:frame",
        "//intrinsic/world/objects:kinematic_object",
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/objects:object_world_ids",
        "//intrinsic/world/objects:world_object",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "preview_context_impl_py",
    srcs = ["preview_context_impl.py"],
    deps = [
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/resources/proto:resource_handle_py_pb2",
        "//intrinsic/skills/proto:prediction_py_pb2",
        "//intrinsic/skills/python:preview_context",
        "//intrinsic/skills/python:skill_canceller",
        "//intrinsic/skills/python:skill_logging_context",
        "//intrinsic/world/proto:object_world_updates_py_pb2",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_ids",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "module_skill_service",
    srcs = ["module_skill_service.py"],
    srcs_version = "PY3",
    deps = [
        ":module_utils",
        ":runtime_data_py",
        ":single_skill_factory_py",
        ":skill_init_py",
        "//intrinsic/skills/python:skill_interface",
        "@com_google_absl_py//absl:app",
        "@com_google_absl_py//absl/flags",
    ],
)

py_library(
    name = "skill_service_impl_py",
    srcs = ["skill_service_impl.py"],
    data = ["@pybind11_abseil//pybind11_abseil:status.so"],
    srcs_version = "PY3",
    deps = [
        ":default_parameters_py",
        ":error_utils_py",
        ":execute_context_impl_py",
        ":get_footprint_context_impl_py",
        ":preview_context_impl_py",
        ":runtime_data_py",
        ":skill_repository_py",
        "//intrinsic/assets:id_utils_py",
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/motion_planning/proto:motion_planner_service_py_pb2_grpc",
        "//intrinsic/skills/proto:error_py_pb2",
        "//intrinsic/skills/proto:footprint_py_pb2",
        "//intrinsic/skills/proto:prediction_py_pb2",
        "//intrinsic/skills/proto:skill_service_py_pb2",
        "//intrinsic/skills/proto:skill_service_py_pb2_grpc",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/skills/python:proto_utils",
        "//intrinsic/skills/python:skill_canceller",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/skills/python:skill_logging_context",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        "//intrinsic/world/python:object_world_client",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
        "@com_google_googleapis//google/longrunning:operations_py_proto",
        "@com_google_googleapis//google/rpc:status_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "proto_utils",
    srcs = ["proto_utils.py"],
    data = ["//intrinsic/util/proto:source_code_info_view_py.so"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/assets:id_utils_py",
        "//intrinsic/skills/proto:skill_manifest_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "@com_google_protobuf//:protobuf_python",
    ],
)

cc_library(
    name = "skill_repository",
    hdrs = ["skill_repository.h"],
    deps = [
        ":runtime_data",
        "//intrinsic/skills/cc:skill_interface",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

py_library(
    name = "skill_repository_py",
    srcs = ["skill_repository.py"],
    deps = [
        ":runtime_data_py",
        "//intrinsic/skills/python:skill_interface",
    ],
)

cc_library(
    name = "runtime_data",
    srcs = ["runtime_data.cc"],
    hdrs = ["runtime_data.h"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_service_config_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:span",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "runtime_data_py",
    srcs = ["runtime_data.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/skills/proto:equipment_py_pb2",
        "//intrinsic/skills/proto:skill_service_config_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "@com_google_protobuf//:protobuf_python",
    ],
)

cc_library(
    name = "single_skill_factory",
    srcs = ["single_skill_factory.cc"],
    hdrs = ["single_skill_factory.h"],
    visibility = ["//visibility:public"],
    deps = [
        ":runtime_data",
        ":skill_repository",
        "//intrinsic/assets:id_utils",
        "//intrinsic/skills/cc:skill_interface",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
    ],
)

py_library(
    name = "single_skill_factory_py",
    srcs = ["single_skill_factory.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":runtime_data_py",
        ":skill_repository_py",
        "//intrinsic/assets:id_utils_py",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/util:decorators",
    ],
)

cc_library(
    name = "skill_init",
    srcs = ["skill_init.cc"],
    hdrs = ["skill_init.h"],
    visibility = ["//visibility:public"],
    deps = [
        ":skill_proto_utils",
        ":skill_registry_client",
        ":skill_repository",
        ":skill_service_impl",
        "//intrinsic/icon/release:file_helpers",
        "//intrinsic/logging:data_logger_client",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_grpc_proto",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/proto:skill_service_config_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:object_world_service_cc_grpc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc_security_base",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "skill_init_py",
    srcs = ["skill_init.py"],
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        ":skill_repository_py",
        ":skill_service_impl_py",
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/motion_planning/proto:motion_planner_service_py_pb2_grpc",
        "//intrinsic/skills/proto:skill_service_config_py_pb2",
        "//intrinsic/skills/proto:skill_service_py_pb2_grpc",
        "//intrinsic/world/proto:object_world_service_py_pb2_grpc",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
    ],
)

cc_library(
    name = "skill_service_impl",
    srcs = ["skill_service_impl.cc"],
    hdrs = ["skill_service_impl.h"],
    deps = [
        ":equipment_utilities",
        ":error_utils",
        ":execute_context_impl",
        ":get_footprint_context_impl",
        ":preview_context_impl",
        ":runtime_data",
        ":skill_registry_client_interface",
        ":skill_repository",
        "//intrinsic/assets:id_utils",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_grpc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/skills/proto:error_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_grpc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/proto:merge",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/status:status_macros_grpc",
        "//intrinsic/util/thread",
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/proto:object_world_service_cc_grpc_proto",
        "@com_github_grpc_grpc//:grpc++_public_hdrs",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/functional:any_invocable",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
        "@com_google_googleapis//google/longrunning:longrunning_cc_proto",
        "@com_google_googleapis//google/rpc:status_cc_proto",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "skill_registry_client",
    srcs = ["skill_registry_client.cc"],
    hdrs = ["skill_registry_client.h"],
    deps = [
        ":skill_registry_client_interface",
        "//intrinsic/skills/cc:client_common",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/internal/proto:behavior_tree_registry_internal_cc_grpc_proto",
        "//intrinsic/skills/internal/proto:skill_registry_internal_cc_grpc_proto",
        "//intrinsic/skills/internal/proto:skill_registry_internal_cc_proto",
        "//intrinsic/skills/proto:behavior_tree_registry_cc_grpc_proto",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_registry_cc_grpc_proto",
        "//intrinsic/skills/proto:skill_registry_cc_proto",
        "//intrinsic/skills/proto:skill_registry_config_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/status:annotate",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "skill_registry_client_interface",
    hdrs = ["skill_registry_client_interface.h"],
    deps = [
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_registry_config_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "skill_proto_utils",
    srcs = ["skill_proto_utils.cc"],
    hdrs = ["skill_proto_utils.h"],
    deps = [
        "//intrinsic/assets/proto:documentation_cc_proto",
        "//intrinsic/assets/proto:id_cc_proto",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/proto:descriptors",
        "//intrinsic/util/proto:source_code_info_view",
        "//intrinsic/util/status:status_macros",
        "@com_github_google_re2//:re2",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:span",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_binary(
    name = "skill_service_config_main",
    srcs = ["skill_service_config_main.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":skill_proto_utils",
        "//intrinsic/assets/proto:id_cc_proto",
        "//intrinsic/icon/release:file_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "//intrinsic/skills/proto:skill_service_config_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_protobuf//:protobuf",
    ],
)

py_package(
    name = "skills_service_py_packages",
    packages = [
        "intrinsic",
        "pybind11_abseil",
    ],
    deps = [
        ":module_skill_service",
        ":module_utils",
        ":skill_service_impl_py",
        "//intrinsic/skills/python:skill_interface",
    ],
)

py_wheel(
    name = "skills_service_wheel",
    distribution = "skills_service",
    requires = [
        "grpcio",
        "google-api-core",
        "numpy",
        "retrying",
    ],
    version = "0.0.1",
    deps = [":skills_service_py_packages"],
)

# The default proto descriptors used by the skill image builder.
proto_source_code_info_transitive_descriptor_set(
    name = "built_skill_proto_descriptors",
    deps = [
        "//intrinsic/math/proto:affine_proto",
        "//intrinsic/math/proto:array_proto",
        "//intrinsic/math/proto:matrix_proto",
        "//intrinsic/math/proto:point_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/math/proto:quaternion_proto",
        "//intrinsic/math/proto:vector2_proto",
        "//intrinsic/math/proto:vector3_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:wrappers_proto",
    ],
)

py_binary(
    name = "module_skill_service_main",
    srcs = ["module_skill_service_main.py"],
    data = [
        ":built_skill_proto_descriptors",
    ],
    srcs_version = "PY3",
    deps = [
        ":module_skill_service",
    ],
)

# The default base image used by the skill image builder for python skills.
python_oci_image(
    name = "built_py_skill_base",
    base = "@distroless_python3",
    binary = ":module_skill_service_main",
    entrypoint = [
        "python3",
        "/ai_intrinsic_sdks~override/intrinsic/skills/internal/module_skill_service_main",
    ],
    # BUG fully-qualified imports on Bzlmod: https://github.com/bazelbuild/rules_python/issues/1679
    symlinks = {
        "/ai_intrinsic_sdks~override/intrinsic/skills/internal/module_skill_service_main": "/intrinsic/skills/internal/module_skill_service_main",
        "/ai_intrinsic_sdks~override/intrinsic/skills/internal/module_skill_service_main.py": "/intrinsic/skills/internal/module_skill_service_main.py",
    },
    workdir = "/",
)
