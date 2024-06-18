# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")
load("//bazel:go_macros.bzl", "go_library")

package(
    default_visibility = ["//visibility:public"],
)

bzl_library(
    name = "services_bzl",
    srcs = ["services.bzl"],
    visibility = ["//visibility:private"],
    deps = [
        "@bazel_skylib//rules:common_settings",
    ],
)

go_library(
    name = "servicegen",
    srcs = ["servicegen.go"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets/services/proto:service_manifest_go_proto",
        "//intrinsic/util/proto:protoio",
        "//intrinsic/util/proto:registryutil",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)

go_binary(
    name = "servicegen_main",
    srcs = ["servicegen_main.go"],
    deps = [
        ":servicegen",
        "//intrinsic/production:intrinsic",
        "@com_github_golang_glog//:go_default_library",
    ],
)
