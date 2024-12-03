# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

go_library(
    name = "assetdescriptions",
    srcs = ["assetdescriptions.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/assets/catalog/proto/v1:asset_catalog_go_grpc_proto",
    ],
)
