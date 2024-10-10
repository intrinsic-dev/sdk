# Copyright 2023 Intrinsic Innovation LLC

load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_proto_library")
load("//bazel:go_macros.bzl", "go_proto_library")

package(
    default_visibility = ["//visibility:public"],
)

proto_library(
    name = "signal_proto",
    srcs = ["signal.proto"],
)

py_proto_library(
    name = "signal_py_pb2",
    deps = [":signal_proto"],
)

cc_proto_library(
    name = "signal_cc_proto",
    deps = [":signal_proto"],
)

go_proto_library(
    name = "signal_go_proto",
    deps = [":signal_proto"],
)

proto_library(
    name = "gpio_service_proto",
    srcs = ["gpio_service.proto"],
    deps = [
        ":signal_proto",
        "@com_google_googleapis//google/rpc:status_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

py_proto_library(
    name = "gpio_service_py_pb2",
    deps = [":gpio_service_proto"],
)

go_proto_library(
    name = "gpio_service_go_proto",
    go_deps = [
        "@org_golang_google_genproto_googleapis_rpc//status",
        "//intrinsic/hardware/gpio:signal_go_proto",
    ],
    deps = [":gpio_service_proto"],
)

cc_proto_library(
    name = "gpio_service_cc_proto",
    deps = [":gpio_service_proto"],
)

cc_grpc_library(
    name = "gpio_service_cc_grpc_proto",
    srcs = [":gpio_service_proto"],
    generate_mocks = True,
    grpc_only = True,
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":gpio_service_cc_proto"],
)
