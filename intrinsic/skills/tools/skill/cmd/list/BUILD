# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "listreleased",
    srcs = [
        "listreleased.go",
    ],
    deps = [
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:cmdutil",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
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
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:cmdutil",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_protobuf//proto",
    ],
)

go_library(
    name = "list",
    srcs = ["list.go"],
    deps = [
        "//intrinsic/skills/proto:skill_registry_go_grpc_proto",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/skills/tools/skill/cmd:cmdutil",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/skills/tools/skill/cmd:listutil",
        "//intrinsic/skills/tools/skill/cmd:skillid",
        "//intrinsic/skills/tools/skill/cmd:solutionutil",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:printer",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@org_golang_google_protobuf//types/known/emptypb:go_default_library",
    ],
)
