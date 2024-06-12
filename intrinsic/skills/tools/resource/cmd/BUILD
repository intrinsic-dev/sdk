# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "bundleimages",
    srcs = ["bundleimages.go"],
    deps = [
        ":readeropener",
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:imageutils",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
    ],
)

go_library(
    name = "readeropener",
    srcs = ["readeropener.go"],
)
