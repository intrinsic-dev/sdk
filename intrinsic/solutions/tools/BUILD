# Copyright 2023 Intrinsic Innovation LLC

# Tools for working with the solution building libraries.

load("//bazel:go_macros.bzl", "go_library", "go_test")

go_library(
    name = "pythonserializer",
    srcs = ["pythonserializer.go"],
    visibility = ["//intrinsic/tools/inctl/cmd/process:__subpackages__"],
    deps = [
        "//intrinsic/executive/proto:behavior_call_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/util/proto:registryutil",
        "@com_github_pkg_errors//:go_default_library",
        "@org_golang_google_protobuf//reflect/protodesc:go_default_library",
        "@org_golang_google_protobuf//reflect/protoreflect:go_default_library",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)

go_test(
    name = "pythonserializer_test",
    srcs = ["pythonserializer_test.go"],
    library = ":pythonserializer",
    deps = [
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/solutions/tools/proto:my_msg_go_proto",
        "@com_github_google_go_cmp//cmp:go_default_library",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//reflect/protodesc:go_default_library",
    ],
)
