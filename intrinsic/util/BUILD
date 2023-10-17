# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_library")

package(
    default_visibility = ["//visibility:public"],
)

cc_library(
    name = "aggregate_type",
    hdrs = ["aggregate_type.h"],
)

cc_test(
    name = "aggregate_type_test",
    srcs = ["aggregate_type_test.cc"],
    deps = [
        ":aggregate_type",
        "//intrinsic/eigenmath",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_library(
    name = "atomic_sequence_num",
    hdrs = ["atomic_sequence_num.h"],
    deps = [":int_id"],
)

cc_library(
    name = "fixed_vector",
    hdrs = ["fixed_vector.h"],
    deps = [
        "@com_google_absl//absl/container:inlined_vector",
        "@com_google_absl//absl/log",
    ],
)

cc_library(
    name = "invalid_until_set",
    hdrs = ["invalid_until_set.h"],
)

cc_library(
    name = "page_fault_info",
    srcs = ["page_fault_info.cc"],
    hdrs = ["page_fault_info.h"],
)

py_library(
    name = "decorators",
    srcs = ["decorators.py"],
    srcs_version = "PY3",
)

cc_library(
    name = "eigen",
    hdrs = ["eigen.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:rotation_utils",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/math:pose3",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "eigen_test",
    srcs = ["eigen_test.cc"],
    deps = [
        ":eigen",
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:rotation_utils",
        "//intrinsic/math:pose3",
        "@com_google_googletest//:gtest_main",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "int_id",
    hdrs = ["int_id.h"],
    deps = [
        "@com_google_absl//absl/meta:type_traits",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "memory_lock",
    hdrs = ["memory_lock.h"],
    deps = [
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "string_type",
    hdrs = ["string_type.h"],
    deps = [
        "@com_google_absl//absl/flags:marshalling",
        "@com_google_absl//absl/hash",
        "@com_google_absl//absl/meta:type_traits",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
    ],
)

cc_library(
    name = "proto_time",
    srcs = ["proto_time.cc"],
    hdrs = ["proto_time.h"],
    deps = [
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)
