# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "cmd",
    srcs = ["root.go"],
    deps = ["@com_github_spf13_cobra//:go_default_library"],
)

go_library(
    name = "start",
    srcs = ["start.go"],
    deps = [
        ":cmd",
        ":imageutil",
        "//intrinsic/kubernetes/workcell_spec:imagetags",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "@com_github_cenkalti_backoff_v4//:go_default_library",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/google:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote/transport:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)

go_library(
    name = "stop",
    srcs = ["stop.go"],
    deps = [
        ":cmd",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
    ],
)

go_library(
    name = "imageutil",
    srcs = ["imageutil.go"],
    deps = [
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
    ],
)
