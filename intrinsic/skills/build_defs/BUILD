# Copyright 2023 Intrinsic Innovation LLC

load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

package(default_visibility = ["//visibility:public"])

bzl_library(
    name = "manifest_bzl",
    srcs = ["manifest.bzl"],
    deps = ["@bazel_skylib//lib:new_sets"],
)

bzl_library(
    name = "skill_bzl",
    srcs = ["skill.bzl"],
    deps = [
        ":manifest_bzl",
        "//intrinsic/util/proto/build_defs:descriptor_set",
        "@bazel_skylib//lib:dicts",
        "@bazel_skylib//lib:new_sets",
        "@bazel_skylib//lib:paths",
        "@io_bazel_rules_docker//container",
        "@io_bazel_rules_docker//lang:image",
    ],
)

cc_binary(
    name = "gen_skill_id",
    srcs = ["gen_skill_id_file.cc"],
    visibility = ["//visibility:public"],
    deps = [
        "//intrinsic/assets/proto:id_cc_proto",
        "//intrinsic/icon/release:file_helpers",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/skills/proto:skill_manifest_cc_proto",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)
