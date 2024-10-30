# Copyright 2023 Intrinsic Innovation LLC

# Testing utilities for skills.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("@rules_python//python:defs.bzl", "py_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(
    default_testonly = True,
)

proto_library(
    name = "echo_skill_proto",
    srcs = ["echo_skill.proto"],
)

cc_proto_library(
    name = "echo_skill_cc_proto",
    visibility = [
        "//intrinsic/executive/engine:__pkg__",
        "//intrinsic/skills/cc:__pkg__",
        "//intrinsic/skills/internal:__pkg__",
    ],
    deps = [":echo_skill_proto"],
)

cc_library(
    name = "echo_skill",
    srcs = ["echo_skill.cc"],
    hdrs = ["echo_skill.h"],
    visibility = ["//intrinsic/skills/internal:__pkg__"],
    deps = [
        ":echo_skill_cc_proto",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_interface_utils",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status:statusor",
        "@com_google_protobuf//:protobuf",
    ],
)

proto_library(
    name = "no_op_skill_proto",
    testonly = False,
    srcs = ["no_op_skill.proto"],
    visibility = ["//intrinsic/skills/build_defs/tests:__pkg__"],
)

cc_proto_library(
    name = "no_op_skill_cc_proto",
    testonly = False,
    visibility = [
        "//intrinsic/executive/engine:__pkg__",
        "//intrinsic/skills/build_defs/tests:__pkg__",
        "//intrinsic/skills/internal:__pkg__",
    ],
    deps = [":no_op_skill_proto"],
)

py_proto_library(
    name = "no_op_skill_py_pb2",
    visibility = [
        "//intrinsic/skills/build_defs/tests:__pkg__",
        "//intrinsic/skills/internal:__pkg__",
    ],
    deps = [":no_op_skill_proto"],
)

go_proto_library(
    name = "no_op_skill_go_proto",
    visibility = [
        "//intrinsic/skills/build_defs:__pkg__",
    ],
    deps = [":no_op_skill_proto"],
)

py_library(
    name = "no_op_skill_py",
    srcs = ["no_op_skill.py"],
    srcs_version = "PY3",
    visibility = [
        "//intrinsic/skills/build_defs/tests:__pkg__",
        "//intrinsic/skills/internal:__pkg__",
    ],
    deps = [
        ":no_op_skill_py_pb2",
        "//intrinsic/skills/proto:footprint_py_pb2",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/skills/python:skill_interface_utils",
        "//intrinsic/util:decorators",
    ],
)

cc_library(
    name = "no_op_skill_cc",
    testonly = False,
    srcs = ["no_op_skill.cc"],
    hdrs = ["no_op_skill.h"],
    visibility = [
        "//intrinsic/performance/qa/apps:__pkg__",
        "//intrinsic/skills/build_defs/tests:__pkg__",
        "//intrinsic/skills/internal:__pkg__",
    ],
    deps = [
        ":no_op_skill_cc_proto",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_interface_utils",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "@com_google_absl//absl/status:statusor",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "map_skill_repository_py",
    testonly = False,
    srcs = ["map_skill_repository.py"],
    visibility = ["//intrinsic/skills/internal:__pkg__"],
    deps = [
        "//intrinsic/skills/internal:runtime_data_py",
        "//intrinsic/skills/internal:single_skill_factory_py",
        "//intrinsic/skills/internal:skill_repository_py",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/util:decorators",
    ],
)

cc_library(
    name = "skill_test_utils_cc",
    testonly = True,
    srcs = ["skill_test_utils.cc"],
    hdrs = ["skill_test_utils.h"],
    visibility = [
        "//intrinsic:public_api_users",
    ],
    deps = [
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_grpc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:execute_request",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/skills/internal:execute_context_impl",
        "//intrinsic/skills/internal:get_footprint_context_impl",
        "//intrinsic/skills/internal:preview_context_impl",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/testing:gtest_wrapper",  # buildcleaner: keep
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/proto:object_world_service_cc_grpc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc_security_base",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "skill_test_utils_test",
    srcs = ["skill_test_utils_test.cc"],
    deps = [
        ":echo_skill",
        ":echo_skill_cc_proto",
        ":skill_test_utils_cc",
        "//intrinsic/assets:id_utils",
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_grpc_proto",
        "//intrinsic/motion_planning/proto:motion_planner_service_cc_proto",
        "//intrinsic/skills/cc:equipment_pack",
        "//intrinsic/skills/cc:skill_canceller",
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/cc:skill_logging_context",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "//intrinsic/util/testing:gtest_wrapper",
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/proto:object_world_service_cc_grpc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/time",
    ],
)
