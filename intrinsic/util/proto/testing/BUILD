# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Test libraries and utilities for situations that deal with proto libraries and
# their generated code.

load("//bazel:go_macros.bzl", "go_library", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(
    default_testonly = True,
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "descriptors_test_proto",
    srcs = ["descriptors_test.proto"],
    deps = [
        ":descriptors_test_left_wrapper_proto",
        ":descriptors_test_right_wrapper_proto",
    ],
)

cc_proto_library(
    name = "descriptors_test_cc_proto",
    deps = [":descriptors_test_proto"],
)

py_proto_library(
    name = "descriptors_test_py_proto",
    deps = [":descriptors_test_proto"],
)

proto_library(
    name = "descriptors_test_left_wrapper_proto",
    srcs = ["descriptors_test_left_wrapper.proto"],
    deps = [
        "@com_google_protobuf//:wrappers_proto",
    ],
)

cc_proto_library(
    name = "descriptors_test_left_wrapper_cc_proto",
    deps = [":descriptors_test_left_wrapper_proto"],
)

py_proto_library(
    name = "descriptors_test_left_wrapper_py_proto",
    deps = [":descriptors_test_left_wrapper_proto"],
)

proto_library(
    name = "descriptors_test_right_wrapper_proto",
    srcs = ["descriptors_test_right_wrapper.proto"],
    deps = [
        "@com_google_protobuf//:wrappers_proto",
    ],
)

cc_proto_library(
    name = "descriptors_test_right_wrapper_cc_proto",
    deps = [":descriptors_test_right_wrapper_proto"],
)

py_proto_library(
    name = "descriptors_test_right_wrapper_py_proto",
    deps = [":descriptors_test_right_wrapper_proto"],
)

proto_library(
    name = "get_text_proto_test_proto",
    srcs = ["get_text_proto_test.proto"],
)

cc_proto_library(
    name = "get_text_proto_test_cc_proto",
    deps = [":get_text_proto_test_proto"],
)

proto_library(
    name = "config_node_to_proto_test_proto",
    srcs = ["config_node_to_proto_test.proto"],
)

cc_proto_library(
    name = "config_node_to_proto_test_cc_proto",
    deps = [":config_node_to_proto_test_proto"],
)

# A, B, C, and D for a diamond dependency.
#
#    A
#  /   \
# B     C
#  \   /
#    D
#
# This situation should be appropriately handled by generated code (typically
# through use of aspects within starlark and namespaces, modules, etc. in the
# specific language).
proto_library(
    name = "diamond_a_proto",
    srcs = ["diamond_a.proto"],
)

proto_library(
    name = "diamond_b_proto",
    srcs = ["diamond_b.proto"],
    deps = [":diamond_a_proto"],
)

proto_library(
    name = "diamond_c_proto",
    srcs = ["diamond_c.proto"],
    deps = [":diamond_a_proto"],
)

proto_library(
    name = "diamond_d_proto",
    srcs = ["diamond_d.proto"],
    deps = [
        ":diamond_b_proto",
        ":diamond_c_proto",
    ],
)

# Has multiple levels of embedded messages an enums that can be used for
# traversing message and file trees.
proto_library(
    name = "embedded_proto",
    srcs = ["embedded.proto"],
)

# Contains a self-referential proto message.  Protos are allowed to have
# themselves as a field, so this helps test the recursive case.
proto_library(
    name = "recursive_proto",
    srcs = ["recursive.proto"],
)

### Language-Specific definitions

go_proto_library(
    name = "diamond_a_go_proto",
    deps = [
        ":diamond_a_proto",
    ],
)

go_proto_library(
    name = "diamond_b_go_proto",
    go_deps = [
        ":diamond_a_go_proto",
    ],
    deps = [
        ":diamond_b_proto",
    ],
)

go_proto_library(
    name = "diamond_c_go_proto",
    go_deps = [
        ":diamond_a_go_proto",
    ],
    deps = [
        ":diamond_c_proto",
    ],
)

go_proto_library(
    name = "diamond_d_go_proto",
    go_deps = [
        ":diamond_b_go_proto",
        ":diamond_c_go_proto",
    ],
    deps = [
        ":diamond_d_proto",
    ],
)

go_proto_library(
    name = "embedded_go_proto",
    deps = [
        ":embedded_proto",
    ],
)

go_proto_library(
    name = "recursive_go_proto",
    deps = [
        ":recursive_proto",
    ],
)

go_library(
    name = "prototestutil",
    srcs = ["proto_test_util.go"],
    deps = [
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//types/known/anypb:go_default_library",
    ],
)
