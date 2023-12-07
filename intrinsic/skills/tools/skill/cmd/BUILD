# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "cmd",
    srcs = ["root.go"],
    deps = [
        "//intrinsic/tools/inctl/cmd:root",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "cmdutil",
    srcs = ["cmdutil.go"],
    deps = [
        ":imageutil",
        "//intrinsic/tools/inctl/util:orgutil",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
    ],
)

go_library(
    name = "solutionutil",
    srcs = ["solutionutil.go"],
    deps = [
        "//intrinsic/frontend/cloud/api:clusterdiscovery_grpc_go_proto",
        "//intrinsic/tools/inctl/cmd/solution",
        "@org_golang_google_grpc//:go_default_library",
    ],
)

go_library(
    name = "registry",
    srcs = ["registry.go"],
    deps = [
        ":imagetransfer",
        ":imageutil",
        "//intrinsic/kubernetes/workcell_spec/proto:image_go_proto",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
    ],
)

go_library(
    name = "dialerutil",
    srcs = ["dialerutil.go"],
    deps = [
        "//intrinsic/tools/inctl/auth",
        "@io_opencensus_go//plugin/ocgrpc:go_default_library",
        "@io_opencensus_go//trace:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//credentials:go_default_library",
        "@org_golang_google_grpc//credentials/insecure:go_default_library",
        "@org_golang_google_grpc//credentials/oauth:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
        "@org_golang_x_oauth2//google:go_default_library",
    ],
)

go_library(
    name = "imageutil",
    srcs = ["imageutil.go"],
    deps = [
        ":imagetransfer",
        "//intrinsic/assets/proto:id_go_proto",
        "//intrinsic/kubernetes/workcell_spec:imagetags",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "//intrinsic/util/proto:protoio",
        "@com_github_google_go_containerregistry//pkg/name:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/tarball:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@io_opencensus_go//trace:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "waitforskill",
    srcs = ["waitforskill.go"],
    deps = [
        "//intrinsic/skills/proto:skill_registry_go_grpc_proto",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)

go_library(
    name = "imagetransfer",
    srcs = ["imagetransfer.go"],
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
    name = "listutil",
    srcs = ["listutil.go"],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/proto:skills_go_proto",
    ],
)

go_library(
    name = "skillid",
    srcs = ["skillid.go"],
    deps = [
        "//intrinsic/assets:idutils",
        "@com_github_google_uuid//:go_default_library",
    ],
)
