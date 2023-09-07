# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(
    default_testonly = True,
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "test_skill_params_proto",
    srcs = ["test_skill_params.proto"],
    deps = [
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/math/proto:pose_proto",
        "//intrinsic/motion_planning/proto:motion_target_proto",
        "//intrinsic/world/proto:collision_settings_proto",
        "//intrinsic/world/proto:object_world_refs_proto",
    ],
)

py_proto_library(
    name = "test_skill_params_py_pb2",
    deps = [":test_skill_params_proto"],
)

proto_source_code_info_transitive_descriptor_set(
    name = "test_skill_params_proto_descriptors",
    deps = [":test_skill_params_proto"],
)
