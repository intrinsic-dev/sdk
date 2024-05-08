# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")
load("//intrinsic/util/proto/build_defs:descriptor_set.bzl", "proto_source_code_info_transitive_descriptor_set")

package(default_visibility = ["//visibility:public"])

# behavior_call
proto_library(
    name = "behavior_call_proto",
    srcs = ["behavior_call.proto"],
    deps = [
        "//intrinsic/skills/proto:footprint_proto",
        "//intrinsic/skills/proto:skills_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

py_proto_library(
    name = "behavior_call_py_pb2",
    deps = [":behavior_call_proto"],
)

cc_proto_library(
    name = "behavior_call_cc_proto",
    deps = [":behavior_call_proto"],
)

go_proto_library(
    name = "behavior_call_go_proto",
    go_deps = [
        "//intrinsic/skills/proto:footprint_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
    ],
    deps = [":behavior_call_proto"],
)

# domain
proto_library(
    name = "domain_proto",
    srcs = ["domain.proto"],
)

py_proto_library(
    name = "domain_py_pb2",
    deps = [":domain_proto"],
)

cc_proto_library(
    name = "domain_cc_proto",
    deps = [":domain_proto"],
)

go_proto_library(
    name = "domain_go_proto",
    deps = [":domain_proto"],
)

# executive_service
proto_library(
    name = "executive_service_proto",
    srcs = ["executive_service.proto"],
    deps = [
        ":behavior_tree_proto",
        ":executive_execution_mode_proto",
        ":run_metadata_proto",
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_googleapis//google/longrunning:operations_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:field_mask_proto",
    ],
)

proto_source_code_info_transitive_descriptor_set(
    name = "executive_service_proto_descriptor_set",
    deps = [":executive_service_proto"],
)

py_proto_library(
    name = "executive_service_py_pb2",
    deps = [":executive_service_proto"],
)

py_grpc_library(
    name = "executive_service_py_pb2_grpc",
    srcs = [":executive_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":executive_service_py_pb2"],
)

go_proto_library(
    name = "executive_service_go_proto",
    go_deps = [
        ":behavior_tree_go_proto",
        ":executive_execution_mode_go_proto",
        ":run_metadata_go_proto",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
    deps = [":executive_service_proto"],
)

go_grpc_library(
    name = "executive_service_go_grpc_proto",
    srcs = [":executive_service_proto"],
    deps = [
        ":behavior_tree_go_proto",
        ":executive_execution_mode_go_proto",
        ":run_metadata_go_proto",
        "@com_google_cloud_go_longrunning//autogen/longrunningpb",
        "@org_golang_google_genproto_googleapis_api//annotations",
    ],
)

# run_metadata
proto_library(
    name = "run_metadata_proto",
    srcs = ["run_metadata.proto"],
    deps = [
        ":behavior_tree_proto",
        ":executive_execution_mode_proto",
        "//intrinsic/logging/proto:context_proto",
    ],
)

py_proto_library(
    name = "run_metadata_py_pb2",
    deps = [":run_metadata_proto"],
)

cc_proto_library(
    name = "run_metadata_cc_proto",
    deps = [":run_metadata_proto"],
)

go_proto_library(
    name = "run_metadata_go_proto",
    go_deps = [
        ":behavior_tree_go_proto",
        ":executive_execution_mode_go_proto",
        "//intrinsic/logging/proto:context_go_proto",
    ],
    deps = [":run_metadata_proto"],
)

# run_response
proto_library(
    name = "run_response_proto",
    srcs = ["run_response.proto"],
)

py_proto_library(
    name = "run_response_py_pb2",
    deps = [":run_response_proto"],
)

cc_proto_library(
    name = "run_response_cc_proto",
    deps = [":run_response_proto"],
)

# blackboard_service
proto_library(
    name = "blackboard_service_proto",
    srcs = ["blackboard_service.proto"],
    deps = [
        "@com_google_googleapis//google/api:annotations_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

py_proto_library(
    name = "blackboard_service_py_pb2",
    deps = [":blackboard_service_proto"],
)

py_grpc_library(
    name = "blackboard_service_py_pb2_grpc",
    srcs = [":blackboard_service_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":blackboard_service_py_pb2"],
)

cc_grpc_library(
    name = "blackboard_service_cc_grpc_proto",
    srcs = [":blackboard_service_proto"],
    grpc_only = True,
    deps = [":blackboard_service_cc_proto"],
)

cc_proto_library(
    name = "blackboard_service_cc_proto",
    deps = [":blackboard_service_proto"],
)

go_proto_library(
    name = "blackboard_service_go_proto",
    go_deps = ["@org_golang_google_genproto_googleapis_api//annotations"],
    deps = [":blackboard_service_proto"],
)

go_grpc_library(
    name = "blackboard_service_go_grpc_proto",
    srcs = [":blackboard_service_proto"],
    deps = [
        ":blackboard_service_go_proto",
        "@org_golang_google_genproto_googleapis_api//annotations",
        "@org_golang_google_protobuf//types/known/anypb",
        "@org_golang_google_protobuf//types/known/emptypb",
    ],
)

# executive_execution_mode
proto_library(
    name = "executive_execution_mode_proto",
    srcs = ["executive_execution_mode.proto"],
)

py_proto_library(
    name = "executive_execution_mode_py_pb2",
    deps = [":executive_execution_mode_proto"],
)

cc_proto_library(
    name = "executive_execution_mode_cc_proto",
    deps = [":executive_execution_mode_proto"],
)

go_proto_library(
    name = "executive_execution_mode_go_proto",
    deps = [":executive_execution_mode_proto"],
)

# executive_state
proto_library(
    name = "executive_state_proto",
    srcs = ["executive_state.proto"],
    deps = [
        "@com_google_googleapis//google/longrunning:operations_proto",
    ],
)

py_proto_library(
    name = "executive_state_py_pb2",
    deps = [":executive_state_proto"],
)

# annotations
proto_library(
    name = "annotations_proto",
    srcs = ["annotations.proto"],
    deps = ["@com_google_protobuf//:descriptor_proto"],
)

cc_proto_library(
    name = "annotations_cc_proto",
    deps = [":annotations_proto"],
)

py_proto_library(
    name = "annotations_py_pb2",
    deps = [":annotations_proto"],
)

go_proto_library(
    name = "annotations_go_proto",
    deps = [":annotations_proto"],
)

# behavior tree
proto_library(
    name = "behavior_tree_proto",
    srcs = ["behavior_tree.proto"],
    deps = [
        ":annotations_proto",
        ":any_list_proto",
        ":any_with_assignments_proto",
        ":behavior_call_proto",
        ":domain_proto",
        ":executive_execution_mode_proto",
        "//intrinsic/skills/proto:skills_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "behavior_tree_cc_proto",
    deps = [":behavior_tree_proto"],
)

py_proto_library(
    name = "behavior_tree_py_pb2",
    deps = [":behavior_tree_proto"],
)

go_proto_library(
    name = "behavior_tree_go_proto",
    go_deps = [
        "//intrinsic/executive/proto:annotations_go_proto",
        "//intrinsic/executive/proto:any_list_go_proto",
        "//intrinsic/executive/proto:any_with_assignments_go_proto",
        "//intrinsic/executive/proto:behavior_call_go_proto",
        "//intrinsic/executive/proto:domain_go_proto",
        "//intrinsic/executive/proto:executive_execution_mode_go_proto",
        "//intrinsic/executive/proto:world_query_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
    ],
    deps = [":behavior_tree_proto"],
)

# WorldQuery
proto_library(
    name = "world_query_proto",
    srcs = ["world_query.proto"],
    deps = ["//intrinsic/world/proto:object_world_refs_proto"],
)

proto_source_code_info_transitive_descriptor_set(
    name = "world_query_proto_descriptor_set",
    deps = [":world_query_proto"],
)

cc_proto_library(
    name = "world_query_cc_proto",
    deps = [":world_query_proto"],
)

py_proto_library(
    name = "world_query_py_pb2",
    deps = [":world_query_proto"],
)

go_proto_library(
    name = "world_query_go_proto",
    go_deps = [
        "//intrinsic/world/proto:object_world_refs_go_proto",
    ],
    deps = [":world_query_proto"],
)

# AnyList
proto_library(
    name = "any_list_proto",
    srcs = ["any_list.proto"],
    deps = ["@com_google_protobuf//:any_proto"],
)

go_proto_library(
    name = "any_list_go_proto",
    deps = [":any_list_proto"],
)

py_proto_library(
    name = "any_list_py_pb2",
    deps = [":any_list_proto"],
)

cc_proto_library(
    name = "any_list_cc_proto",
    deps = [":any_list_proto"],
)

# AnyWithAssignments
proto_library(
    name = "any_with_assignments_proto",
    srcs = ["any_with_assignments.proto"],
    deps = ["@com_google_protobuf//:any_proto"],
)

py_proto_library(
    name = "any_with_assignments_py_pb2",
    deps = [":any_with_assignments_proto"],
)

cc_proto_library(
    name = "any_with_assignments_cc_proto",
    deps = [":any_with_assignments_proto"],
)

go_proto_library(
    name = "any_with_assignments_go_proto",
    deps = [":any_with_assignments_proto"],
)

# test message
proto_library(
    name = "test_message_proto",
    srcs = ["test_message.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:duration_proto",
    ],
)

proto_source_code_info_transitive_descriptor_set(
    name = "test_message_proto_descriptor_set",
    deps = [":test_message_proto"],
)

cc_proto_library(
    name = "test_message_cc_proto",
    deps = [
        ":test_message_proto",
    ],
)

py_proto_library(
    name = "test_message_py_pb2",
    deps = [":test_message_proto"],
)

proto_library(
    name = "proto_builder_proto",
    srcs = ["proto_builder.proto"],
    deps = ["@com_google_protobuf//:descriptor_proto"],
)

py_proto_library(
    name = "proto_builder_py_pb2",
    deps = [":proto_builder_proto"],
)

py_grpc_library(
    name = "proto_builder_py_pb2_grpc",
    srcs = [":proto_builder_proto"],
    grpc_library = requirement("grpcio"),
    deps = [":proto_builder_py_pb2"],
)

cc_proto_library(
    name = "proto_builder_cc_proto",
    deps = [":proto_builder_proto"],
)

cc_grpc_library(
    name = "proto_builder_cc_grpc_proto",
    srcs = [":proto_builder_proto"],
    grpc_only = True,
    deps = [":proto_builder_cc_proto"],
)

go_proto_library(
    name = "proto_builder_go_proto",
    deps = [":proto_builder_proto"],
)

go_grpc_library(
    name = "proto_builder_go_grpc_proto",
    srcs = [":proto_builder_proto"],
    deps = ["@io_bazel_rules_go//proto/wkt:descriptor_go_proto"],
)
