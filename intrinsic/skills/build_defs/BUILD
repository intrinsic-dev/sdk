# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")
load("//bazel:go_macros.bzl", "go_library", "go_test")

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
        "//bazel:container_bzl",
        "//bazel:python_oci_image_bzl",
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
        "//intrinsic/util/proto:sourcecodeinfoview",
        "@com_github_golang_glog//:go_default_library",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)

go_binary(
    name = "skillbundlegen",
    srcs = ["skillbundlegen.go"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:idutils",
        "//intrinsic/production:intrinsic",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/util/proto:protoio",
        "@com_github_golang_glog//:go_default_library",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
    ],
)

go_library(
    name = "skillserviceconfiggen",
    srcs = ["skillserviceconfiggen.go"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/skills/proto:skill_service_config_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/util/proto:protoio",
        "//intrinsic/util/proto:sourcecodeinfoview",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//proto",
    ],
)

go_binary(
    name = "skillserviceconfiggen_main",
    srcs = ["skillserviceconfiggen_main.go"],
    visibility = ["//visibility:public"],
    deps = [
        ":skillserviceconfiggen",
        "//intrinsic/production:intrinsic",
        "@com_github_golang_glog//:go_default_library",
    ],
)

go_library(
    name = "skilllabelsgen",
    srcs = ["skilllabelsgen.go"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "@com_github_golang_glog//:go_default_library",
    ],
)

go_binary(
    name = "skilllabelsgen_main",
    srcs = ["skilllabelsgen_main.go"],
    visibility = ["//visibility:public"],
    deps = [
        ":skilllabelsgen",
        "//intrinsic/production:intrinsic",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/util/proto:protoio",
        "@com_github_golang_glog//:go_default_library",
    ],
)

go_test(
    name = "skilllabelsgen_test",
    srcs = ["skilllabelsgen_test.go"],
    data = [
        "//intrinsic/skills/build_defs/tests:no_op_skill_cc_manifest",
        "//intrinsic/skills/build_defs/tests:no_op_skill_py_manifest",
    ],
    deps = [
        ":skilllabelsgen",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
        "//intrinsic/util:runfiles",
        "//intrinsic/util/proto:protoio",
    ],
)
