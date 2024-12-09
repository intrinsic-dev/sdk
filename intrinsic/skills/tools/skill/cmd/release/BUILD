# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "release",
    srcs = ["release.go"],
    deps = [
        "//intrinsic/assets:bundleio",
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets:idutils",
        "//intrinsic/assets:imagetransfer",
        "//intrinsic/assets:imageutils",
        "//intrinsic/assets/catalog/proto/v1:asset_catalog_go_grpc_proto",
        "//intrinsic/assets/proto:asset_type_go_proto",
        "//intrinsic/assets/proto:metadata_go_proto",
        "//intrinsic/assets/proto:release_tag_go_proto",
        "//intrinsic/skills/proto:processed_skill_manifest_go_proto",
        "//intrinsic/skills/tools/resource/cmd:bundleimages",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd/directupload",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_google_go_containerregistry//pkg/v1/google:go_default_library",
        "@com_github_google_go_containerregistry//pkg/v1/remote:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)
