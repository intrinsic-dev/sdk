# Copyright 2023 Intrinsic Innovation LLC

# StatusBuilder to build Intrinsic platform error reports

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("//bazel:go_macros.bzl", "go_library", "go_proto_library")

package(
    default_visibility = ["//visibility:public"],
)

cc_library(
    name = "status_builder",
    srcs = ["status_builder.cc"],
    hdrs = ["status_builder.h"],
    deps = [
        "//intrinsic/icon/release:source_location",
        "//intrinsic/logging/proto:context_cc_proto",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/debugging:stacktrace",
        "@com_google_absl//absl/debugging:symbolize",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:log_entry",
        "@com_google_absl//absl/log:log_sink",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "status_macros",
    hdrs = ["status_macros.h"],
    deps = [
        ":status_builder",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/base:core_headers",
    ],
)

cc_library(
    name = "status_conversion_proto",
    srcs = ["status_conversion_proto.cc"],
    hdrs = ["status_conversion_proto.h"],
    deps = [
        ":status_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/strings:string_view",
    ],
)

cc_library(
    name = "status_conversion_rpc",
    srcs = ["status_conversion_rpc.cc"],
    hdrs = ["status_conversion_rpc.h"],
    deps = [
        "//intrinsic/util/proto:type_url",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_googleapis//google/rpc:status_cc_proto",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "status_conversion_grpc",
    srcs = ["status_conversion_grpc.cc"],
    hdrs = ["status_conversion_grpc.h"],
    deps = [
        ":status_conversion_rpc",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_googleapis//google/rpc:code_cc_proto",
        "@com_google_googleapis//google/rpc:status_cc_proto",
    ],
)

cc_test(
    name = "status_conversion_grpc_test",
    srcs = ["status_conversion_grpc_test.cc"],
    deps = [
        ":status_conversion_grpc",
        "//intrinsic/util/proto:type_url",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings:cord",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "status_conversion_rpc_test",
    srcs = ["status_conversion_rpc_test.cc"],
    deps = [
        ":status_conversion_rpc",
        "//intrinsic/util/proto:type_url",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/status",
        "@com_google_googleapis//google/rpc:code_cc_proto",
        "@com_google_googleapis//google/rpc:status_cc_proto",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "log_if_error",
    hdrs = ["log_if_error.h"],
    deps = [
        ":status_builder",
        ":status_macros",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "return",
    hdrs = ["return.h"],
    deps = ["@com_google_absl//absl/status"],
)

cc_library(
    name = "ret_check",
    srcs = ["ret_check.cc"],
    hdrs = ["ret_check.h"],
    deps = [
        ":status_builder",
        ":status_macros",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "annotate",
    srcs = ["annotate.cc"],
    hdrs = ["annotate.h"],
    deps = [
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/strings:string_view",
    ],
)

cc_library(
    name = "status_builder_grpc",
    srcs = ["status_builder_grpc.cc"],
    hdrs = ["status_builder_grpc.h"],
    deps = [
        ":status_builder",
        ":status_conversion_grpc",
        "//intrinsic/icon/release:source_location",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/log:log_sink",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "status_macros_grpc",
    hdrs = ["status_macros_grpc.h"],
    deps = [
        ":status_builder",
        ":status_builder_grpc",
        ":status_conversion_grpc",
        ":status_macros",
        "//intrinsic/icon/release:source_location",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "ret_check_grpc",
    srcs = ["ret_check_grpc.cc"],
    hdrs = ["ret_check_grpc.h"],
    deps = [
        ":ret_check",
        ":status_builder",
        ":status_builder_grpc",
        ":status_macros_grpc",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/status",
    ],
)

cc_test(
    name = "annotate_test",
    srcs = ["annotate_test.cc"],
    deps = [
        ":annotate",
        ":status_builder",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings:cord",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "ret_check_test",
    srcs = ["ret_check_test.cc"],
    deps = [
        ":ret_check",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/log:scoped_mock_log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_test(
    name = "status_builder_test",
    srcs = ["status_builder_test.cc"],
    deps = [
        ":status_builder",
        "//intrinsic/icon/release:source_location",
        "//intrinsic/util/proto:type_url",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/log:log_entry",
        "@com_google_absl//absl/log:log_sink",
        "@com_google_absl//absl/log:scoped_mock_log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:cord",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "status_macros_test",
    srcs = ["status_macros_test.cc"],
    deps = [
        ":status_builder",
        ":status_macros",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_test(
    name = "status_macros_grpc_test",
    srcs = ["status_macros_grpc_test.cc"],
    deps = [
        ":status_builder",
        ":status_builder_grpc",
        ":status_conversion_grpc",
        ":status_macros_grpc",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

proto_library(
    name = "status_proto",
    srcs = ["status.proto"],
)

proto_library(
    name = "extended_status_proto",
    srcs = ["extended_status.proto"],
    deps = [
        "//intrinsic/logging/proto:context_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

go_proto_library(
    name = "extended_status_go_proto",
    go_deps = [
        "//intrinsic/logging/proto:context_go_proto",
    ],
    deps = [":extended_status_proto"],
)

cc_proto_library(
    name = "extended_status_cc_proto",
    deps = [":extended_status_proto"],
)

py_proto_library(
    name = "extended_status_py_pb2",
    deps = [":extended_status_proto"],
)

cc_proto_library(
    name = "status_cc_proto",
    deps = [":status_proto"],
)

py_library(
    name = "status_exception",
    srcs = ["status_exception.py"],
    deps = [
        ":extended_status_py_pb2",
        "//intrinsic/logging/proto:context_py_pb2",
    ],
)

py_test(
    name = "status_exception_test",
    srcs = ["status_exception_test.py"],
    deps = [
        ":extended_status_py_pb2",
        ":status_exception",
        "//intrinsic/logging/proto:context_py_pb2",
        "//intrinsic/solutions/testing:compare",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

go_library(
    name = "extstatus",
    srcs = ["extstatus.go"],
    deps = [
        ":extended_status_go_proto",
        "//intrinsic/logging/proto:context_go_proto",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)
