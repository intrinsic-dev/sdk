# Copyright 2023 Intrinsic Innovation LLC

# An acl engine using Authzed SpiceDB.

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = [
    "//visibility:public",
])

go_library(
    name = "org",
    srcs = ["org.go"],
    deps = [
        ":cookies",
        "//intrinsic/frontend/go:origin",
        "@com_github_golang_glog//:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)

go_library(
    name = "jwt",
    srcs = ["jwt.go"],
    deps = ["@com_github_pkg_errors//:go_default_library"],
)

go_library(
    name = "identity",
    srcs = ["identity.go"],
    deps = [
        ":cookies",
        ":jwt",
        ":org",
        "@com_github_golang_glog//:go_default_library",
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
    ],
)

go_library(
    name = "groups",
    srcs = ["groups.go"],
    deps = [":org"],
)

go_library(
    name = "relationships",
    srcs = ["relationships.go"],
)

go_library(
    name = "schema",
    srcs = ["schema.go"],
    embedsrcs = [
        "//intrinsic/kubernetes/acl/schemas:schema",  # keep
    ],
)

go_library(
    name = "roles",
    srcs = ["roles.go"],
    data = ["//intrinsic/kubernetes/acl/schemas"],
    embedsrcs = [
        "//intrinsic/kubernetes/acl/schemas",  # keep
    ],
    deps = [
        "@com_github_pkg_errors//:go_default_library",
        "@in_gopkg_yaml_v2//:go_default_library",
        "@org_golang_x_exp//maps",
    ],
)

go_library(
    name = "schemaload",
    srcs = ["schemaload.go"],
    deps = [
        ":schema",
        "@in_gopkg_yaml_v2//:go_default_library",
    ],
)

go_library(
    name = "bindings",
    srcs = ["bindings.go"],
    deps = [
        ":relationships",
        ":schema",
        "//intrinsic/kubernetes/acl/service:encoding",
    ],
)

go_library(
    name = "grant",
    srcs = ["grant.go"],
    deps = [
        ":schema",
        "//intrinsic/kubernetes/acl/service/api:read_api_go_grpc_proto",
        "//intrinsic/kubernetes/acl/service/api:read_api_go_proto",
        "//intrinsic/kubernetes/acl/service/api:write_api_go_grpc_proto",
    ],
)

go_library(
    name = "serviceaccounts",
    srcs = ["serviceaccounts.go"],
    deps = [":identity"],
)

go_library(
    name = "cookies",
    srcs = ["cookies.go"],
    deps = ["@org_golang_google_grpc//metadata:go_default_library"],
)

go_library(
    name = "serviceauth",
    srcs = ["serviceauth.go"],
    deps = [
        "@org_golang_google_api//idtoken:go_default_library",
        "@org_golang_google_grpc//metadata:go_default_library",
        "@org_golang_x_oauth2//:go_default_library",
    ],
)

go_library(
    name = "interceptors",
    srcs = ["interceptors.go"],
    deps = [
        ":identity",
        "//intrinsic/stats/go:slogattrs",
        "@io_opencensus_go//trace:go_default_library",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_grpc//codes:go_default_library",
        "@org_golang_google_grpc//status:go_default_library",
    ],
)
