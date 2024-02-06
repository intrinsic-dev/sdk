# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "skill",
    srcs = ["skill.go"],
    deps = [
        ":root",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd/create",
        "//intrinsic/skills/tools/skill/cmd/list",
        "//intrinsic/skills/tools/skill/cmd/list:listreleased",
        "//intrinsic/skills/tools/skill/cmd/list:listreleasedversions",
        "//intrinsic/skills/tools/skill/cmd/load",
        "//intrinsic/skills/tools/skill/cmd/load:unload",
        "//intrinsic/skills/tools/skill/cmd/logs",
        "//intrinsic/skills/tools/skill/cmd/release",
    ],
)

go_library(
    name = "root",
    srcs = ["root.go"],
    deps = [
        "//intrinsic/production:intrinsic",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@io_opencensus_go//trace:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
        "@org_golang_x_exp//slices",
    ],
)
