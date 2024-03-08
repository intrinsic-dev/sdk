# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_test")

package(default_visibility = ["//visibility:public"])

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

exports_files(
    srcs = [
        "BUILD",
        "BUILD.eigen",
        "BUILD.libarchive",
        "BUILD.sysroot",
        "BUILD.workspace_root",
        "LICENSE",
        "README.md",
        "WORKSPACE",
        "copy.bara.sky",
        "extension_for_com_google_googleapis.bzl",
        "extension_for_io_bazel_rules_docker.bzl",
        "extension_for_rules_oci.bzl",
        "go.mod",
        "go.sum",
        "grpc_synchronized_test.py",
        "intrinsic.bazelrc",
        "intrinsic.bazelversion",
        "intrinsic.gitignore",
        "non_module_deps.bzl",
        "requirements.in",
        "requirements.txt",
    ],
)
