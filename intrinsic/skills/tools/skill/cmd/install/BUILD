# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "install",
    srcs = ["install.go"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/assets/proto:installed_assets_go_grpc_proto",
        "//intrinsic/skills/tools/resource/cmd:bundleimages",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:waitforskill",
        "//intrinsic/skills/tools/skill/cmd/directupload",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)

go_library(
    name = "uninstall",
    srcs = ["uninstall.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:imageutils",
        "//intrinsic/kubernetes/workcell_spec/proto:installer_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:skillio",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
