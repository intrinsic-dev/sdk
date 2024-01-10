# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "notebook",
    srcs = [
        "create.go",
        "notebook.go",
    ],
    embedsrcs = [
        "//intrinsic/tools/inctl/cmd/notebook/templates:empty_notebook.ipynb.template",  #keep
    ],
    deps = [
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:cobrautil",
        "//intrinsic/tools/inctl/util:printer",
        "//intrinsic/tools/inctl/util:templateutil",
        "@com_github_spf13_cobra//:go_default_library",
    ],
)
