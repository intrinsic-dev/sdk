# Copyright 2023 Intrinsic Innovation LLC

# Python wrapper for the intrinsic pubsub c++ library.

load("@rules_python//python:defs.bzl", "py_test")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")

package(default_visibility = ["//visibility:public"])

pybind_extension(
    name = "pubsub",
    srcs = ["pubsub.cc"],
    deps = [
        "//intrinsic/platform/pubsub",
        "//intrinsic/platform/pubsub:subscription",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@pybind11_abseil//pybind11_abseil:no_throw_status",
        "@pybind11_abseil//pybind11_abseil:status_casters",
        "@pybind11_protobuf//pybind11_protobuf:native_proto_caster",
    ],
)

py_test(
    name = "pubsub_test",
    srcs = ["pubsub_test.py"],
    data = [
        ":pubsub.so",
        "//intrinsic/platform/common/proto:test_cc_proto",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    tags = [
        "noasan",
        "nomsan",
    ],
    deps = [
        "//intrinsic/platform/common/proto:test_py_pb2",
        "//intrinsic/solutions/testing:compare",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
    ],
)
