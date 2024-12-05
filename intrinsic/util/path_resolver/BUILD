# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("//bazel:go_macros.bzl", "go_library", "go_test")

package(default_visibility = ["//visibility:public"])

exports_files(
    srcs = [
        # go/keep-sorted start
        "BUILD",
        "path_resolver.cc",
        "path_resolver.go",
        "path_resolver.h",
        "path_resolver.py",
        "path_resolver_test.cc",
        "path_resolver_test.go",
        "path_resolver_test.py",
        # go/keep-sorted end
    ],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "path_resolver",
    srcs = [
        "path_resolver.cc",
    ],
    hdrs = [
        "path_resolver.h",
    ],
    deps = [
        "@bazel_tools//tools/cpp/runfiles",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/strings",
        "@or_tools//ortools/base:path",
    ],
)

cc_test(
    name = "path_resolver_test",
    srcs = ["path_resolver_test.cc"],
    data = ["path_resolver_test.cc"],
    deps = [
        ":path_resolver",
        "//intrinsic/util/testing:gtest_wrapper_main",
    ],
)

py_library(
    name = "path_resolver_py",
    srcs = ["path_resolver.py"],
    deps = [
        "@rules_python//python/runfiles",
    ],
)

py_test(
    name = "path_resolver_py_test",
    srcs = ["path_resolver_test.py"],
    data = [
        "path_resolver_test.py",
    ],
    main = "path_resolver_test.py",
    deps = [
        ":path_resolver_py",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

go_library(
    name = "pathresolver",  # Coding style suggests to avoid using underscores in package names: http://golang.org/doc/effective_go.html#package-names
    srcs = ["path_resolver.go"],
    deps = [
        "@io_bazel_rules_go//go/runfiles:go_default_library",
    ],
)

go_test(
    name = "path_resolver_go_test",
    srcs = ["path_resolver_test.go"],
    data = ["path_resolver_test.go"],
    deps = [":pathresolver"],
)
