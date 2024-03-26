# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = [
    "//intrinsic/frontend:__subpackages__",
    "//intrinsic/kubernetes:__subpackages__",
    "//intrinsic/skills/tools/skill:__subpackages__",
    "//intrinsic/solutions:__subpackages__",
    "//intrinsic/tools/inctl:__subpackages__",
])

go_proto_library(
    name = "orgdiscovery_api_go_proto",
    deps = [
        ":orgdiscovery_api_proto",
    ],
)

proto_library(
    name = "orgdiscovery_api_proto",
    srcs = ["orgdiscovery_api.proto"],
    deps = ["@com_google_protobuf//:empty_proto"],
)

go_grpc_library(
    name = "orgdiscovery_grpc_go_proto",
    srcs = [":orgdiscovery_api_proto"],
    deps = [":orgdiscovery_api_go_proto"],
)

proto_library(
    name = "clusterdiscovery_api_proto",
    srcs = ["clusterdiscovery_api.proto"],
)

go_proto_library(
    name = "clusterdiscovery_api_go_proto",
    deps = [":clusterdiscovery_api_proto"],
)

go_grpc_library(
    name = "clusterdiscovery_grpc_go_proto",
    srcs = [":clusterdiscovery_api_proto"],
    deps = [":clusterdiscovery_api_go_proto"],
)

proto_library(
    name = "projectdiscovery_api_proto",
    srcs = ["projectdiscovery_api.proto"],
    deps = [
        "@com_google_protobuf//:empty_proto",
    ],
)

go_proto_library(
    name = "projectdiscovery_api_go_proto",
    deps = [":projectdiscovery_api_proto"],
)

go_grpc_library(
    name = "projectdiscovery_grpc_go_proto",
    srcs = [":projectdiscovery_api_proto"],
    deps = [
        ":projectdiscovery_api_go_proto",
    ],
)

proto_library(
    name = "solutiondiscovery_api_proto",
    srcs = ["solutiondiscovery_api.proto"],
    deps = [":clusterdiscovery_api_proto"],
)

py_proto_library(
    name = "solutiondiscovery_api_py_pb2",
    deps = [":solutiondiscovery_api_proto"],
)

py_grpc_library(
    name = "solutiondiscovery_api_py_pb2_grpc",
    srcs = [":solutiondiscovery_api_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":solutiondiscovery_api_py_pb2"],
)

go_proto_library(
    name = "solutiondiscovery_api_go_proto",
    go_deps = [":clusterdiscovery_api_go_proto"],
    deps = [
        ":solutiondiscovery_api_proto",
    ],
)

go_grpc_library(
    name = "solutiondiscovery_grpc_go_proto",
    srcs = [":solutiondiscovery_api_proto"],
    deps = [
        ":clusterdiscovery_grpc_go_proto",
        ":solutiondiscovery_api_go_proto",
    ],
)

proto_library(
    name = "clusterdeletion_api_proto",
    srcs = ["clusterdeletion_api.proto"],
    deps = ["@com_google_protobuf//:empty_proto"],
)

go_proto_library(
    name = "clusterdeletion_api_go_proto",
    deps = [":clusterdeletion_api_proto"],
)

go_grpc_library(
    name = "clusterdeletion_grpc_go_proto",
    srcs = [":clusterdeletion_api_proto"],
    deps = [":clusterdeletion_api_go_proto"],
)
