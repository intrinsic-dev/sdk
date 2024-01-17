# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")
load("@rules_python//python:defs.bzl", "py_library")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "any",
    hdrs = ["any.h"],
    deps = [
        ":merge",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "descriptors",
    srcs = ["descriptors.cc"],
    hdrs = ["descriptors.h"],
    deps = [
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_protobuf//:protobuf",
    ],
)

py_library(
    name = "descriptors_py",
    srcs = ["descriptors.py"],
    srcs_version = "PY3",
    deps = ["@com_google_protobuf//:protobuf_python"],
)

cc_library(
    name = "get_text_proto",
    srcs = ["get_text_proto.cc"],
    hdrs = ["get_text_proto.h"],
    deps = [
        ":any",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "merge",
    srcs = ["merge.cc"],
    hdrs = ["merge.h"],
    deps = [
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/types:span",
        "@com_google_protobuf//:protobuf",
    ],
)

go_library(
    name = "protoio",
    srcs = ["protoio.go"],
    deps = [
        "@com_github_protocolbuffers_txtpbfmt//parser:go_default_library",
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)

go_library(
    name = "resolvercache",
    srcs = ["resolver_cache.go"],
    deps = [
        ":registryutil",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)

go_library(
    name = "registryutil",
    srcs = ["registryutil.go"],
    deps = [
        ":protoio",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//reflect/protodesc:go_default_library",
        "@org_golang_google_protobuf//reflect/protoreflect:go_default_library",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
        "@org_golang_google_protobuf//types/dynamicpb:go_default_library",
    ],
)

cc_library(
    name = "source_code_info_view",
    srcs = ["source_code_info_view.cc"],
    hdrs = ["source_code_info_view.h"],
    deps = [
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_protobuf//:protobuf",
        "@com_google_protobuf//:protobuf_lite",
    ],
)

pybind_extension(
    name = "source_code_info_view_py",
    srcs = ["source_code_info_view_py.cc"],
    deps = [
        ":source_code_info_view",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
        "@com_google_protobuf//:protobuf",
        "@com_google_protobuf//:protobuf_lite",
        "@pybind11_abseil//pybind11_abseil:absl_casters",
        "@pybind11_abseil//pybind11_abseil:status_casters",
        "@pybind11_protobuf//pybind11_protobuf:wrapped_proto_caster",
    ],
)
