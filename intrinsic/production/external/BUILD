# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_test")

package(default_visibility = ["//visibility:public"])

exports_files(
    srcs = [
        "intrinsic.bazelrc",
        "intrinsic.bazelversion",
    ],
    visibility = [
        "//intrinsic/tools/inctl/cmd/bazel/templates:__pkg__",
    ],
)

py_test(
    name = "grpc_synchronized_py_test",
    size = "small",
    srcs = ["grpc_synchronized_test.py"],
    args = [
        "--deps-0",
        "$(location //bazel:deps_0.bzl)",
        "--requirements-in",
        "$(location //:requirements.in)",
        "--requirements-txt",
        "$(location //:requirements.txt)",
    ],
    data = [
        "//:requirements.in",
        "//:requirements.txt",
        "//bazel:deps_0.bzl",
    ],
    main = "grpc_synchronized_test.py",
    python_version = "PY3",
    srcs_version = "PY3",
)
