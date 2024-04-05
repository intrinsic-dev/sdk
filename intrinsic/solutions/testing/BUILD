# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(
    default_testonly = True,
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "test_skill_params_proto",
    srcs = ["test_skill_params.proto"],
    deps = [
        "//intrinsic/executive/proto:test_message_proto",
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
    visibility = [
        "//intrinsic/executive/clips_cpp:__subpackages__",
        "//intrinsic/solutions:__subpackages__",
    ],
    deps = [":test_skill_params_proto"],
)

py_library(
    name = "compare",
    srcs = ["compare.py"],
    srcs_version = "PY3",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "compare_test",
    srcs = ["compare_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":compare",
        "//intrinsic/executive/proto:test_message_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
    ],
)
