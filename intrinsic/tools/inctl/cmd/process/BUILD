# Copyright 2023 Intrinsic Innovation LLC

load("//bazel:go_macros.bzl", "go_library")

package(default_visibility = ["//intrinsic/tools/inctl:__subpackages__"])

go_library(
    name = "process",
    srcs = [
        "process.go",
        "process_get.go",
        "process_set.go",
    ],
    deps = [
        "//intrinsic/executive/proto:annotations_go_proto",
        "//intrinsic/executive/proto:behavior_tree_go_proto",
        "//intrinsic/executive/proto:executive_service_go_grpc_proto",
        "//intrinsic/executive/proto:executive_service_go_proto",
        "//intrinsic/executive/proto:run_metadata_go_proto",
        "//intrinsic/skills/proto:skill_registry_go_grpc_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/skills/tools/skill/cmd:dialerutil",
        "//intrinsic/skills/tools/skill/cmd:solutionutil",
        "//intrinsic/solutions/tools:pythonserializer",
        "//intrinsic/tools/inctl/cmd:root",
        "//intrinsic/tools/inctl/util:orgutil",
        "//intrinsic/util/proto:registryutil",
        "@com_github_pkg_errors//:go_default_library",
        "@com_github_spf13_cobra//:go_default_library",
        "@com_github_spf13_viper//:go_default_library",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@io_bazel_rules_go//proto/wkt:descriptor_go_proto",
        "@org_golang_google_grpc//:go_default_library",
        "@org_golang_google_protobuf//encoding/prototext:go_default_library",
        "@org_golang_google_protobuf//proto",
        "@org_golang_google_protobuf//reflect/protodesc:go_default_library",
        "@org_golang_google_protobuf//reflect/protoreflect:go_default_library",
        "@org_golang_google_protobuf//reflect/protoregistry:go_default_library",
    ],
)
