# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "listreleased",
    srcs = [
        "listreleased.go",
    ],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets/proto:release_tag_go_proto",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/skills/catalog/proto:skill_catalog_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:listutil",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)

go_library(
    name = "listreleasedversions",
    srcs = [
        "listreleasedversions.go",
    ],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/assets/proto:view_go_proto",
        "//intrinsic/skills/catalog/proto:skill_catalog_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:listutil",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "list",
    srcs = ["list.go"],
    deps = [
        "//intrinsic/assets:clientutils",
        "//intrinsic/assets:cmdutils",
        "//intrinsic/skills/proto:skill_registry_go_grpc_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:listutil",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
