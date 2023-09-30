# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

# Protos for internal skill framework types.

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "skill_registry_internal_proto",
    srcs = ["skill_registry_internal.proto"],
    deps = [
        "//intrinsic/skills/proto:equipment_proto",
        "//intrinsic/skills/proto:skill_registry_config_proto",
        "//intrinsic/skills/proto:skills_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

cc_proto_library(
    name = "skill_registry_internal_cc_proto",
    deps = [":skill_registry_internal_proto"],
)

cc_grpc_library(
    name = "skill_registry_internal_cc_grpc_proto",
    srcs = [":skill_registry_internal_proto"],
    grpc_only = True,
    deps = [":skill_registry_internal_cc_proto"],
)

py_proto_library(
    name = "skill_registry_internal_py_pb2",
    deps = [":skill_registry_internal_proto"],
)

py_grpc_library(
    name = "skill_registry_internal_py_pb2_grpc",
    srcs = [":skill_registry_internal_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":skill_registry_internal_py_pb2"],
)

proto_library(
    name = "behavior_tree_registry_internal_proto",
    srcs = ["behavior_tree_registry_internal.proto"],
    deps = ["//intrinsic/executive/proto:behavior_tree_proto"],
)

cc_proto_library(
    name = "behavior_tree_registry_internal_cc_proto",
    deps = [":behavior_tree_registry_internal_proto"],
)

cc_grpc_library(
    name = "behavior_tree_registry_internal_cc_grpc_proto",
    srcs = [":behavior_tree_registry_internal_proto"],
    grpc_only = True,
    deps = [":behavior_tree_registry_internal_cc_proto"],
)

py_proto_library(
    name = "behavior_tree_registry_internal_py_pb2",
    deps = [":behavior_tree_registry_internal_proto"],
)

py_grpc_library(
    name = "behavior_tree_registry_internal_py_pb2_grpc",
    srcs = [":behavior_tree_registry_internal_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":behavior_tree_registry_internal_py_pb2"],
)
