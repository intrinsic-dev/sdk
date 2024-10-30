# Copyright 2023 Intrinsic Innovation LLC

load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "my_msg_proto",
    srcs = ["my_msg.proto"],
)

go_proto_library(
    name = "my_msg_go_proto",
    deps = [":my_msg_proto"],
)
