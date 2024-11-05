# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("//bazel:container.bzl", "container_image")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_library", "go_proto_library", "go_test")
load("//bazel:python_oci_image.bzl", "python_oci_image")
load("//intrinsic/assets/services/build_defs:services.bzl", "intrinsic_service")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "calc_server_proto",
    srcs = ["calc_server.proto"],
)

cc_proto_library(
    name = "calc_server_cc_proto",
    deps = [":calc_server_proto"],
)

cc_grpc_library(
    name = "calc_server_cc_grpc_proto",
    srcs = [":calc_server_proto"],
    generate_mocks = True,
    grpc_only = True,
    deps = [":calc_server_cc_proto"],
)

cc_library(
    name = "calc_server",
    srcs = ["calc_server.cc"],
    hdrs = ["calc_server.h"],
    deps = [
        ":calc_server_cc_grpc_proto",
        ":calc_server_cc_proto",
        "//intrinsic/resources/proto:runtime_context_cc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/log",
    ],
)

cc_test(
    name = "calc_server_test",
    srcs = ["calc_server_test.cc"],
    deps = [
        ":calc_server",
        ":calc_server_cc_grpc_proto",
        ":calc_server_cc_proto",
        "//intrinsic/util/proto:parse_text_proto",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
    ],
)

cc_binary(
    name = "calc_server_main",
    srcs = ["calc_server_main.cc"],
    deps = [
        ":calc_server",
        ":calc_server_cc_proto",
        "//intrinsic/icon/release:file_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/resources/proto:runtime_context_cc_proto",
        "//intrinsic/util/proto:any",
        "//intrinsic/util/status:status_macros",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc_security_base",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:string_view",
    ],
)

container_image(
    name = "calculator-image",
    base = "@distroless_base",
    data_path = "/",
    entrypoint = ["intrinsic/assets/services/examples/calcserver/calc_server_main"],
    files = [":calc_server_main"],
)

intrinsic_service(
    name = "calculator_service",
    default_config = ":calc_default_config.textproto",
    images = [
        "//intrinsic/assets/services/examples/calcserver:calculator-image.tar",
    ],
    manifest = ":calc_manifest.textproto",
    deps = [
        ":calc_server_proto",
    ],
)

go_proto_library(
    name = "calc_server_go_proto",
    deps = [":calc_server_proto"],
)

go_grpc_library(
    name = "calc_server_go_grpc_proto",
    srcs = [":calc_server_proto"],
    deps = [":calc_server_go_proto"],
)

go_library(
    name = "calcserver",
    srcs = ["calcserver.go"],
    deps = [
        ":calc_server_go_grpc_proto",
        "//intrinsic/assets/services/proto/v1:dynamic_reconfiguration_go_grpc_proto",
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)

go_test(
    name = "calcserver_test",
    srcs = ["calcserver_test.go"],
    library = ":calcserver",
    deps = [
        ":calc_server_go_grpc_proto",
        ":calc_server_go_proto",
        "//intrinsic/assets/services/proto/v1:dynamic_reconfiguration_go_grpc_proto",
        "//intrinsic/testing:grpctest",
        "@com_github_google_go_cmp//cmp:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//testing/protocmp:go_default_library",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)

go_binary(
    name = "calcserver_main_go",
    srcs = ["calcserver_main.go"],
    deps = [
        ":calc_server_go_grpc_proto",
        ":calc_server_go_proto",
        ":calcserver",
        "//intrinsic/assets/services/proto/v1:dynamic_reconfiguration_go_grpc_proto",
        "//intrinsic/kubernetes:intrinsic",
        "//intrinsic/resources/proto:runtime_context_go_proto",
        "//intrinsic/util/proto:protoio",
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//reflection:go_default_library",
    ],
)

container_image(
    name = "calc_server_go_image",
    base = "@distroless_base",
    data_path = "/",
    entrypoint = [
        "intrinsic/assets/services/examples/calcserver/calcserver_main_go_/calcserver_main_go",
    ],
    files = [
        ":calcserver_main_go",
    ],
)

intrinsic_service(
    name = "calculator_go",
    default_config = ":calc_default_config.textproto",
    images = [
        ":calc_server_go_image.tar",
    ],
    manifest = "calc_manifest_go.textproto",
    deps = [
        ":calc_server_proto",
    ],
)

py_proto_library(
    name = "calc_server_py_pb2",
    deps = [":calc_server_proto"],
)

py_grpc_library(
    name = "calc_server_py_pb2_grpc",
    srcs = [":calc_server_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":calc_server_py_pb2"],
)

py_library(
    name = "calc_server_py",
    srcs = ["calc_server.py"],
    deps = [
        ":calc_server_py_pb2",
        ":calc_server_py_pb2_grpc",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
    ],
)

py_test(
    name = "calc_server_test_py",
    srcs = ["calc_server_test.py"],
    main = "calc_server_test.py",
    deps = [
        ":calc_server_py",
        ":calc_server_py_pb2",
        ":calc_server_py_pb2_grpc",
        "@ai_intrinsic_sdks_pip_deps//portpicker",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_absl_py//absl/testing:parameterized",
    ],
)

py_binary(
    name = "calc_server_main_py",
    srcs = ["calc_server_main.py"],
    main = "calc_server_main.py",
    deps = [
        ":calc_server_py",
        ":calc_server_py_pb2",
        ":calc_server_py_pb2_grpc",
        "//intrinsic/resources/proto:runtime_context_py_pb2",
        requirement("grpcio"),
        "@com_google_absl_py//absl:app",
        "@com_google_absl_py//absl/flags",
        "@com_google_absl_py//absl/logging",
    ],
)

python_oci_image(
    name = "calc_server_py_image",
    base = "@distroless_base",
    binary = ":calc_server_main_py",
    data_path = "/",
)

intrinsic_service(
    name = "calculator_py",
    default_config = ":calc_default_config.textproto",
    images = [
        ":calc_server_py_image.tar",
    ],
    manifest = "calc_manifest_py.textproto",
    deps = [
        ":calc_server_proto",
    ],
)

intrinsic_service(
    name = "calculator_no_sim_example",
    default_config = ":calc_default_config.textproto",
    images = [
        ":calculator-image.tar",
        "//intrinsic/resources:noop_image.tar",
    ],
    manifest = "calc_manifest_no_sim_example.textproto",
    deps = [
        ":calc_server_proto",
    ],
)
