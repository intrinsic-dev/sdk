# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "resource_registry_proto",
    srcs = ["resource_registry.proto"],
    deps = [
        ":resource_handle_proto",
        "//intrinsic/assets/proto:metadata_proto",
        "//intrinsic/assets/proto:view_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

go_proto_library(
    name = "resource_registry_go_proto",
    go_deps = [
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
    ],
    deps = [":resource_registry_proto"],
)

go_grpc_library(
    name = "resource_registry_go_grpc_proto",
    srcs = [":resource_registry_proto"],
    deps = [
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)

py_proto_library(
    name = "resource_registry_py_pb2",
    deps = [":resource_registry_proto"],
)

py_grpc_library(
    name = "resource_registry_py_pb2_grpc",
    srcs = [":resource_registry_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":resource_registry_py_pb2"],
)

cc_proto_library(
    name = "resource_registry_cc_proto",
    deps = [":resource_registry_proto"],
)

cc_grpc_library(
    name = "resource_registry_cc_grpc",
    srcs = [":resource_registry_proto"],
    grpc_only = True,
    deps = [":resource_registry_cc_proto"],
)

proto_library(
    name = "resource_handle_proto",
    srcs = ["resource_handle.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "resource_handle_cc_proto",
    deps = [":resource_handle_proto"],
)

py_proto_library(
    name = "resource_handle_py_pb2",
    deps = [":resource_handle_proto"],
)

go_proto_library(
    name = "resource_handle_go_proto",
    deps = [":resource_handle_proto"],
)
