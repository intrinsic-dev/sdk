# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "directupload",
    srcs = [
        "discovery.go",
        "monitor.go",
        "transfer.go",
    ],
    deps = [
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/storage/artifacts/client",
        "//intrinsic/storage/artifacts/proto:articat_go_grpc_proto",
        "//intrinsic/storage/artifacts/proto:artifact_go_grpc_proto",
        "@com_github_cenkalti_backoff_v4//:go_default_library",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_uber_go_atomic//:go_default_library",
    ],
)
