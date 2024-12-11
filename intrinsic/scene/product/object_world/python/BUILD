# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = [
    "//visibility:public",
])

py_library(
    name = "product_utils",
    srcs = ["product_utils.py"],
    deps = [
        "//intrinsic/math/python:data_types",
        "//intrinsic/scene/product/proto:product_world_object_data_py_pb2",
        "//intrinsic/scene/proto/v1:scene_object_py_pb2",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_ids",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_protobuf//:protobuf_python",
    ],
)
