# Copyright 2023 Intrinsic Innovation LLC

load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "source_location",
    hdrs = ["source_location.h"],
    deps = ["@com_google_absl//absl/base:core_headers"],
)

cc_library(
    name = "file_helpers",
    hdrs = ["file_helpers.h"],
    deps = [
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//src/google/protobuf/io",
    ],
)

py_library(
    name = "file_helpers_py",
    srcs = ["file_helpers.py"],
    deps = [
        "@com_google_protobuf//:protobuf_python",
    ],
)

cc_binary(
    name = "reset_simulation",
    srcs = ["reset_simulation.cc"],
    deps = [
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/simulation/service/proto:simulation_service_cc_grpc_proto",
        "//intrinsic/simulation/service/proto:simulation_service_cc_proto",
        "//intrinsic/util/grpc",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "grpc_time_support",
    srcs = ["grpc_time_support.cc"],
    hdrs = ["grpc_time_support.h"],
    deps = [
        "@com_github_grpc_grpc//:gpr",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/time",
    ],
)

# A trivial test that prints hello world. This test only exists to validate
# that our release codebase's python toolchain works.
py_test(
    name = "hello_world_py_test",
    srcs = ["hello_world_py_test.py"],
)

# A trivial test that prints hello world. This test only exists to validate
# that our release codebase's C++ toolchain works.
cc_test(
    name = "hello_world_cc_test",
    srcs = ["hello_world.cc"],
)
