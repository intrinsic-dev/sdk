# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

# Helper utilities for handling testing.

go_library(
    name = "testio",
    srcs = ["test_io.go"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "@io_bazel_rules_go//go/tools/bazel:go_default_library",
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

cc_library(
    name = "gtest_wrapper",
    testonly = 1,
    hdrs = ["gtest_wrapper.h"],
    visibility = ["//visibility:public"],
    deps = [
        ":status_payload_matchers",
        "@com_github_inazarenko_protobuf_matchers//protobuf-matchers",
        "@com_google_absl//absl/status:status_matchers",
        "@com_google_cel_cpp//internal:testing",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_library(
    name = "status_payload_matchers",
    testonly = 1,
    hdrs = ["status_payload_matchers.h"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = [
        "//intrinsic/util/proto:type_url",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:cord",
        "@com_google_googleapis//google/rpc:status_cc_proto",
        "@com_google_googletest//:gtest",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "status_payload_matchers_test",
    srcs = ["status_payload_matchers_test.cc"],
    deps = [
        ":status_payload_matchers",
        "//intrinsic/util/proto:type_url",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:cord",
        "@com_google_protobuf//:protobuf",
    ],
)
