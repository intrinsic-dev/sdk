# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "product_proto",
    srcs = ["product.proto"],
    deps = [
        "@com_google_protobuf//:struct_proto",
    ],
)

cc_proto_library(
    name = "product_cc_proto",
    deps = [":product_proto"],
)

go_proto_library(
    name = "product_go_proto",
    deps = [
        ":product_proto",
    ],
)

py_proto_library(
    name = "product_py_pb2",
    deps = [":product_proto"],
)

proto_library(
    name = "product_service_proto",
    srcs = ["product_service.proto"],
    deps = [
        ":product_proto",
        "//intrinsic/assets/proto:id_proto",
        "//intrinsic/geometry/proto:primitives_proto",
        "//intrinsic/scene/proto/v1:scene_object_proto",
        "//intrinsic/scene/proto/v1:scene_object_updates_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:struct_proto",
    ],
)

cc_proto_library(
    name = "product_service_cc_proto",
    deps = [":product_service_proto"],
)

cc_grpc_library(
    name = "product_service_cc_grpc_proto",
    srcs = [":product_service_proto"],
    grpc_only = True,
    deps = [":product_service_cc_proto"],
)

go_proto_library(
    name = "product_service_go_proto",
    go_deps = [
        ":product_go_proto",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_updates_go_proto",
    ],
    deps = [":product_service_proto"],
)

go_grpc_library(
    name = "product_service_go_grpc_proto",
    srcs = [":product_service_proto"],
    deps = [
        ":product_go_proto",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_updates_go_proto",
        "@org_golang_google_protobuf//types/known/emptypb",
        "@org_golang_google_protobuf//types/known/structpb",
    ],
)

py_proto_library(
    name = "product_service_py_pb2",
    deps = [":product_service_proto"],
)

py_grpc_library(
    name = "product_service_py_pb2_grpc",
    srcs = [":product_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":product_service_py_pb2"],
)

proto_library(
    name = "product_world_object_data_proto",
    srcs = ["product_world_object_data.proto"],
    deps = ["@com_google_protobuf//:struct_proto"],
)

cc_proto_library(
    name = "product_world_object_data_cc_proto",
    deps = [":product_world_object_data_proto"],
)

py_proto_library(
    name = "product_world_object_data_py_pb2",
    deps = [":product_world_object_data_proto"],
)
