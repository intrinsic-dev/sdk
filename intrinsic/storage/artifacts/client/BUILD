# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

# Artifacts service client for inctl
package(default_visibility = ["//visibility:public"])

go_library(
    name = "client",
    srcs = [
        "adapter.go",
        "monitor.go",
        "nstask.go",
        "task.go",
        "uploader.go",
    ],
    deps = [
        "//intrinsic/storage/artifacts/internal:utils",
        "//intrinsic/storage/artifacts/proto:artifact_go_grpc_proto",
        "//intrinsic/storage/artifacts/proto:artifact_go_proto",
        "@com_github_cenkalti_backoff_v4//:go_default_library",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/partial:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/types:go_default_library",
        "@com_github_pborman_uuid//:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_x_sync//errgroup:go_default_library",
        "@org_uber_go_atomic//:go_default_library",
    ],
)
