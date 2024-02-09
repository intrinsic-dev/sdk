# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "auth",
    srcs = [
        "auth.go",
        "list.go",
        "login.go",
        "print.go",
        "revoke.go",
        "update.go",
    ],
    deps = [
        "//intrinsic/frontend/cloud/api:orgdiscovery_grpc_go_proto",
        "//intrinsic/frontend/cloud/api:projectdiscovery_grpc_go_proto",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/auth",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/tools/inctl/util:printer",
        "//intrinsic/tools/inctl/util:viperutil",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//types/known/emptypb:go_default_library",
        "@org_uber_go_multierr//:go_default_library",
    ],
)
