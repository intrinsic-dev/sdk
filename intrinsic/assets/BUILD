# Copyright 2023 Intrinsic Innovation LLC

# Common code for assets (e.g., skills, resources).

load("//bazel:go_macros.bzl", "go_library")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "auth",
    srcs = ["auth.go"],
    visibility = [
        "//intrinsic/assets:__subpackages__",
        "//intrinsic/resources:__subpackages__",
        "//intrinsic/skills:__subpackages__",
    ],
    deps = [
        "//intrinsic/tools/inctl/auth",
        "@org_golang_google_grpc//credentials:go_default_library",
    ],
)

cc_library(
    name = "id_utils",
    srcs = ["id_utils.cc"],
    hdrs = ["id_utils.h"],
    deps = [
        "//intrinsic/assets/proto:id_cc_proto",
        "//intrinsic/util/status:annotate",
        "//intrinsic/util/status:status_macros",
        "@com_github_google_re2//:re2",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)

py_library(
    name = "id_utils_py",
    srcs = ["id_utils.py"],
    deps = ["//intrinsic/assets/proto:id_py_pb2"],
)

go_library(
    name = "idutils",
    srcs = ["idutils.go"],
    deps = [
        "//intrinsic/assets/proto:id_go_proto",
        "@org_golang_x_exp//slices",
    ],
)

go_library(
    name = "metadatafieldlimits",
    srcs = ["metadata_field_limits.go"],
)
