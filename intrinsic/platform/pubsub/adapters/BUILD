# Copyright 2023 Intrinsic Innovation LLC

# PubSub adapters implementations.

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "pubsub_proto",
    srcs = ["pubsub.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "pubsub_cc_proto",
    deps = [":pubsub_proto"],
)

go_proto_library(
    name = "pubsub_go_proto",
    deps = [":pubsub_proto"],
)
