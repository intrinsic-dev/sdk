# Copyright 2023 Intrinsic Innovation LLC

# Common code for assets (e.g., skills, resources).

load("@rules_python//python:defs.bzl", "py_library")
load("//bazel:go_macros.bzl", "go_library")

go_library(
    name = "clientutils",
    srcs = ["clientutils.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        ":cmdutils",
        "//intrinsic/frontend/cloud/api:clusterdiscovery_api_go_grpc_proto",
        "//intrinsic/frontend/cloud/api:solutiondiscovery_api_go_grpc_proto",
        "//intrinsic/tools/inctl/auth",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_google_go_containerregistry//pkg/authn:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/google:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)

go_library(
    name = "cmdutils",
    srcs = ["cmdutils.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        ":imagetransfer",
        ":imageutils",
        "//intrinsic/tools/inctl/util:orgutil",
        "@com_github_google_go_containerregistry//pkg/authn:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/google:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
    ],
)

cc_library(
    name = "id_utils",
    srcs = ["id_utils.cc"],
    hdrs = ["id_utils.h"],
    visibility = ["//intrinsic:public_api_users"],
    deps = [
        "//intrinsic/assets/proto:id_cc_proto",
        "//intrinsic/util/status:annotate",
        "//intrinsic/util/status:status_macros",
        "@boringssl//:crypto",
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
    visibility = ["//intrinsic:public_api_users"],
    deps = ["//intrinsic/assets/proto:id_py_pb2"],
)

go_library(
    name = "idutils",
    srcs = ["idutils.go"],
    visibility = ["//intrinsic:public_api_users"],
    deps = [
        "//intrinsic/assets/proto:id_go_proto",
        "@org_golang_x_exp//slices",
    ],
)

go_library(
    name = "metadatafieldlimits",
    srcs = ["metadata_field_limits.go"],
    visibility = ["//intrinsic:internal_api_users"],
)

go_library(
    name = "imagetransfer",
    srcs = ["imagetransfer.go"],
    visibility = [
        "//intrinsic:internal_api_users",
        "//intrinsic:public_api_users",
    ],
    deps = [
        "@com_github_cenkalti_backoff_v4//:go_default_library",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote/transport:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
    ],
)

go_library(
    name = "imageutils",
    srcs = ["imageutils.go"],
    visibility = ["//intrinsic:public_api_users"],
    deps = [
        ":idutils",
        ":imagetransfer",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/kubernetes/workcell_spec:imagetags",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_rs_xid//:go_default_library",
        "@io_opencensus_go//trace:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "typeutils",
    srcs = ["typeutils.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        "//intrinsic/assets/proto:asset_type_go_proto",
        "@org_golang_x_exp//slices",
    ],
)

go_library(
    name = "bundleio",
    srcs = ["bundle_io.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/assets/services/proto:service_manifest_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "//intrinsic/util/archive:tartooling",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//types/known/anypb",
    ],
)

go_library(
    name = "version",
    srcs = ["version.go"],
    visibility = ["//intrinsic:internal_api_users"],
    deps = [
        ":idutils",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/resources/proto:resource_registry_go_grpc_proto",
        "@org_golang_google_protobuf//proto",
    ],
)
