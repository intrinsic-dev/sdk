# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Python wrapper for public API.

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

# Unless we have more mature tests, the library remains unreleased.
package(default_visibility = [
    "//visibility:public",
])

py_library(
    name = "image_utils",
    srcs = ["image_utils.py"],
    deps = [
        "//intrinsic/perception/proto:image_buffer_py_pb2",
        requirement("pillow"),
        requirement("numpy"),
    ],
)
