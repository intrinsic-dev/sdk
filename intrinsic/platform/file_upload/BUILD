# Copyright 2023 Intrinsic Innovation LLC

load("@io_bazel_rules_go//go:def.bzl", "go_binary")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "file_upload_service_proto",
    srcs = ["file_upload_service.proto"],
)

go_proto_library(
    name = "file_upload_service_go_proto",
    deps = [":file_upload_service_proto"],
)

go_grpc_library(
    name = "file_upload_service_go_grpc_proto",
    srcs = [":file_upload_service_proto"],
    deps = [":file_upload_service_go_proto"],
)

go_binary(
    name = "file_upload_cli",
    srcs = [
        "file_upload_cli.go",
    ],
    deps = [
        ":file_upload_service_go_grpc_proto",
        ":file_upload_service_go_proto",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_google_subcommands//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
    ],
)
