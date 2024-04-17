# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "service_manifest_proto",
    srcs = ["service_manifest.proto"],
    deps = [
        "//intrinsic/assets/proto:asset_tag_proto",
        "//intrinsic/assets/proto:documentation_proto",
        "//intrinsic/assets/proto:id_proto",
        "//intrinsic/assets/proto:vendor_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:descriptor_proto",
    ],
)

go_proto_library(
    name = "service_manifest_go_proto",
    go_deps = [
        "//intrinsic/assets/proto:asset_tag_go_proto",
        "//intrinsic/assets/proto:documentation_go_proto",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/proto:vendor_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
    ],
    deps = [":service_manifest_proto"],
)

py_proto_library(
    name = "service_manifest_py_pb2",
    deps = [":service_manifest_proto"],
)
