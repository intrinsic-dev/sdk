# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library", "go_test")

package(default_visibility = ["//visibility:public"])

go_library(
    name = "auth",
    srcs = [
        "auth.go",
        "token_source.go",
        "tokenshttp.go",
    ],
    deps = [
        "//intrinsic/kubernetes/acl:jwt",
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_grpc//credentials:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)

go_library(
    name = "authtest",
    testonly = True,
    srcs = ["authtest.go"],
    deps = [":auth"],
)

go_test(
    name = "auth_test",
    srcs = [
        "auth_test.go",
        "token_source_test.go",
        "tokenshttp_test.go",
    ],
    library = ":auth",
    deps = [
        "//intrinsic/kubernetes/acl/testing:jwttesting",
        "@com_github_google_go_cmp//cmp:go_default_library",
        "@com_github_google_go_cmp//cmp/cmpopts:go_default_library",
        "@com_github_pborman_uuid//:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)
