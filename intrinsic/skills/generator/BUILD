# Copyright 2023 Intrinsic Innovation LLC

# Provides generators for creating skill source code.

load("//bazel:go_macros.bzl", "go_library")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")
load("@rules_python//python:defs.bzl", "py_library")

package(
    default_visibility = ["//visibility:private"],
)

go_library(
    name = "gen",
    srcs = ["gen.go"],
    embedsrcs = [
        "skill_service_main.py.tmpl",
        "skill_service_main_tmpl.cc",
    ],
    deps = [
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "@org_golang_google_protobuf//proto",
    ],
)

go_binary(
    name = "skill_service_generator",
    srcs = ["skill_service_generator.go"],
    visibility = ["//visibility:public"],
    deps = [
        ":gen",
        "//intrinsic/production:intrinsic",
        "@com_github_golang_glog//:go_default_library",
    ],
)

py_library(
    name = "app",
    srcs = ["app.py"],
    visibility = ["//visibility:public"],
    deps = ["@com_google_absl_py//absl:app"],
)
