# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_test")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(
    default_testonly = True,
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "test_message_dep",
    srcs = ["test_message_dep.proto"],
)

cc_proto_library(
    name = "test_message_dep_cc_proto",
    deps = [":test_message_dep"],
)

proto_library(
    name = "test_message_proto",
    srcs = ["test_message.proto"],
    deps = [
        ":test_message_dep",
        "@com_google_protobuf//:duration_proto",
    ],
)

py_proto_library(
    name = "test_message_py_pb2",
    deps = [":test_message_proto"],
)

proto_source_code_info_transitive_descriptor_set(
    name = "test_message_proto_descriptors",
    deps = [":test_message_proto"],
)

py_test(
    name = "source_code_info_present_test",
    srcs = ["source_code_info_present_test.py"],
    data = [
        ":test_message_proto_descriptors",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@com_google_absl_py//absl/flags",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)
