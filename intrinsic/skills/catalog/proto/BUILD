# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "skill_catalog_proto",
    srcs = ["skill_catalog.proto"],
    deps = [
        "//intrinsic/assets/proto:id_proto",
        "//intrinsic/assets/proto:metadata_proto",
        "//intrinsic/assets/proto:release_tag_proto",
        "//intrinsic/assets/proto:view_proto",
        "//intrinsic/executive/proto:behavior_tree_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_proto",
        "//intrinsic/skills/proto:skill_manifest_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

cc_proto_library(
    name = "skill_catalog_cc_proto",
    deps = [":skill_catalog_proto"],
)

cc_grpc_library(
    name = "skill_catalog_cc_grpc_proto",
    srcs = [":skill_catalog_proto"],
    grpc_only = True,
    deps = [":skill_catalog_cc_proto"],
)

go_proto_library(
    name = "skill_catalog_go_proto",
    go_deps = [
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:release_tag_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
    ],
    deps = [":skill_catalog_proto"],
)

go_grpc_library(
    name = "skill_catalog_go_grpc_proto",
    srcs = [":skill_catalog_proto"],
    deps = [
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:release_tag_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "//intrinsic/skills/proto:skill_manifest_go_proto",
    ],
)
