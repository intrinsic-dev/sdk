# Copyright 2023 Intrinsic Innovation LLC

# Testing utilities for skills.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library")

package(
    default_testonly = True,
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "no_op_skill_proto",
    testonly = False,
    srcs = ["no_op_skill.proto"],
)

cc_proto_library(
    name = "no_op_skill_cc_proto",
    testonly = False,
    deps = [":no_op_skill_proto"],
)

py_proto_library(
    name = "no_op_skill_py_pb2",
    deps = [":no_op_skill_proto"],
)

py_library(
    name = "no_op_skill_py",
    srcs = ["no_op_skill.py"],
    srcs_version = "PY3",
    deps = [
        ":no_op_skill_py_pb2",
        "//intrinsic/skills/proto:footprint_py_pb2",
        "//intrinsic/skills/python:skill_interface",
        "//intrinsic/skills/python:skill_interface_utils",
        "//intrinsic/util:decorators",
    ],
)

cc_library(
    name = "no_op_skill",
    testonly = False,
    srcs = ["no_op_skill.cc"],
    hdrs = ["no_op_skill.h"],
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
    srcs = ["skill_test_utils.cc"],
    hdrs = ["skill_test_utils.h"],
    deps = [
        "//intrinsic/skills/cc:skill_interface",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_protobuf//:protobuf",
    ],
)
