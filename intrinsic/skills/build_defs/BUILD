# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")

package(default_visibility = ["//visibility:public"])

bzl_library(
    name = "manifest_bzl",
    srcs = ["manifest.bzl"],
    deps = [
        "//intrinsic/util/proto/build_defs:descriptor_set",
    ],
)

bzl_library(
    name = "skill_bzl",
    srcs = ["skill.bzl"],
    deps = [
        ":manifest_bzl",
        "//intrinsic/util/proto/build_defs:descriptor_set",
    ],
)

go_binary(
    name = "gen_skill_id",
    srcs = ["gen_skill_id.go"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/production:intrinsic",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/util/proto:protoio",
        "@com_github_golang_glog//:go_default_library",
    ],
)

go_binary(
    name = "skillmanifestgen",
    srcs = ["skillmanifestgen.go"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:metadatafieldlimits",
        "//intrinsic/production:intrinsic",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/util/proto:protoio",
        "//intrinsic/util/proto:registryutil",
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)
