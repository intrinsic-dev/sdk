# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# This package is to provide a consistent way throughout Intrinsic components to
# store structured data about errors.

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "error_report_proto",
    srcs = ["error_report.proto"],
    deps = [
        "@com_google_googleapis//google/rpc:status_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "error_report_cc_proto",
    deps = [":error_report_proto"],
)

py_proto_library(
    name = "error_report_py_pb2",
    deps = [":error_report_proto"],
)
