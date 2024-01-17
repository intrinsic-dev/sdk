# Copyright 2023 Intrinsic Innovation LLC

# This package contains shared protos for different hardware integrations.

load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")

# The visibility of this entire package is limited since before continued usage of the pattern which
# is being exposed here we want to explore if proto options
# (https://engdoc.corp.google.com/eng/doc/devguide/proto/proto.md?cl=head#options) offer a better
# way to expose ranges of allowed values and unit names.
package(default_visibility = ["//visibility:public"])

exports_files(
    srcs = [
        "BUILD",
        "settings.proto",
    ],
    visibility = ["//intrinsic/production:__subpackages__"],
)

proto_library(
    name = "settings_proto",
    srcs = ["settings.proto"],
)

cc_proto_library(
    name = "settings_cc_proto",
    deps = [":settings_proto"],
)

py_proto_library(
    name = "settings_py_pb2",
    deps = [":settings_proto"],
)

go_proto_library(
    name = "settings_go_proto",
    deps = [":settings_proto"],
)
