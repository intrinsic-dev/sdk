# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

# AssetCatalog protos.

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "asset_catalog_proto",
    srcs = ["asset_catalog.proto"],
    deps = [
        "//intrinsic/assets/proto:asset_tag_proto",
        "//intrinsic/assets/proto:asset_type_proto",
        "//intrinsic/assets/proto:id_proto",
        "//intrinsic/assets/proto:metadata_proto",
        "//intrinsic/assets/proto:view_proto",
        "//intrinsic/assets/services/proto:service_manifest_proto",
        "//intrinsic/skills/proto:processed_skill_manifest_proto",
    ],
)

cc_proto_library(
    name = "asset_catalog_cc_proto",
    deps = [":asset_catalog_proto"],
)

cc_grpc_library(
    name = "asset_catalog_cc_grpc_proto",
    srcs = [":asset_catalog_proto"],
    generate_mocks = True,
    grpc_only = True,
    deps = [":asset_catalog_cc_proto"],
)

go_proto_library(
    name = "asset_catalog_go_proto",
    go_deps = [
        "//intrinsic/assets/proto:asset_tag_go_proto",
        "//intrinsic/assets/proto:asset_type_go_proto",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/assets/services/proto:service_manifest_go_proto",
        "//intrinsic/skills/proto:processed_skill_manifest_go_proto",
    ],
    deps = [":asset_catalog_proto"],
)

go_grpc_library(
    name = "asset_catalog_go_grpc_proto",
    srcs = [":asset_catalog_proto"],
    deps = [
        "//intrinsic/assets/proto:asset_tag_go_proto",
        "//intrinsic/assets/proto:asset_type_go_proto",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/assets/services/proto:service_manifest_go_proto",
        "//intrinsic/skills/proto:processed_skill_manifest_go_proto",
    ],
)

py_proto_library(
    name = "asset_catalog_py_pb2",
    deps = [":asset_catalog_proto"],
)

py_grpc_library(
    name = "asset_catalog_py_pb2_grpc",
    srcs = [":asset_catalog_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":asset_catalog_py_pb2"],
)
