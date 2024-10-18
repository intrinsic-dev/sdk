# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "product_client",
    srcs = ["product_client.py"],
    deps = [
        "//intrinsic/scene/product/proto:product_py_pb2",
        "//intrinsic/scene/product/proto:product_service_py_pb2",
        "//intrinsic/scene/product/proto:product_service_py_pb2_grpc",
        "//intrinsic/scene/proto:scene_object_py_pb2",
        "//intrinsic/util/grpc:error_handling",
        requirement("grpcio"),
    ],
)
