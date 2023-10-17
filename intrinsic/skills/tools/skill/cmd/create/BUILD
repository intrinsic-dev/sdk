# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "create",
    srcs = ["create.go"],
    embedsrcs = [
        "templates/BUILD_cc_fragment.template",  #keep
        "templates/BUILD_py_fragment.template",  #keep
        "templates/skill_cc.template",  #keep
        "templates/skill_cc_manifest.template",  #keep
        "templates/skill_h.template",  #keep
        "templates/skill_params_proto.template",  #keep
        "templates/skill_py.template",  #keep
        "templates/skill_py_manifest.template",  #keep
    ],
    deps = [
        "//intrinsic/assets:idutils",
        "//intrinsic/skills/tools/skill/cmd",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/cmd/bazel",
        "//intrinsic/tools/inctl/cmd/version",
        "//intrinsic/tools/inctl/util:printer",
        "//intrinsic/tools/inctl/util:templateutil",
        "@com_github_bazelbuild_buildtools//edit:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_stoewer_go_strcase//:go_default_library",
    ],
)
