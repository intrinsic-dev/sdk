# Copyright 2023 Intrinsic Innovation LLC

# StatusBuilder to build Intrinsic platform error reports

package(
    default_visibility = ["//visibility:public"],
)

cc_library(
    name = "status_builder",
    srcs = ["status_builder.cc"],
    hdrs = ["status_builder.h"],
    deps = [
        "//intrinsic/icon/release:source_location",
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
        "@com_google_absl//absl/status",
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
        ":status_builder_grpc",
        ":status_macros_grpc",
        "//intrinsic/icon/release:source_location",
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

cc_proto_library(
    name = "status_cc_proto",
    deps = [":status_proto"],
)
