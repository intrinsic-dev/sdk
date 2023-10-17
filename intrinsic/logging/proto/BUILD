# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("//bazel:go_macros.bzl", "go_proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "log_item_proto",
    srcs = ["log_item.proto"],
    deps = [
        ":blob_proto",
        ":context_proto",
        ":flowstate_event",
        "//intrinsic/executive/proto:executive_state_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/icon/proto:part_status_proto",
        "//intrinsic/logging/errors/proto:error_report_proto",
        "//intrinsic/motion_planning/proto:motion_planner_service_proto",
        "//intrinsic/perception/proto:frame_proto",
        "//intrinsic/perception/proto:hand_eye_calibration",
        "//intrinsic/perception/proto:pose_estimation_result",
        "//intrinsic/skills/proto:skill_service_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "log_item_cc_proto",
    deps = [":log_item_proto"],
)

py_proto_library(
    name = "log_item_py_pb2",
    deps = [":log_item_proto"],
)

proto_library(
    name = "blob_proto",
    srcs = ["blob.proto"],
)

cc_proto_library(
    name = "blob_cc_proto",
    deps = [":blob_proto"],
)

py_proto_library(
    name = "blob_py_pb2",
    deps = [":blob_proto"],
)

proto_library(
    name = "context_proto",
    srcs = ["context.proto"],
)

proto_library(
    name = "flowstate_event",
    srcs = ["flowstate_event.proto"],
    visibility = ["//intrinsic/production:__subpackages__"],
)

cc_proto_library(
    name = "flowstate_event_cc_proto",
    deps = [":flowstate_event"],
)

go_proto_library(
    name = "flowstate_event_go_proto",
    deps = [":flowstate_event"],
)

py_proto_library(
    name = "flowstate_event_py_pb2",
    deps = [":flowstate_event"],
)

py_proto_library(
    name = "context_py_pb2",
    deps = [":context_proto"],
)

cc_proto_library(
    name = "context_cc_proto",
    deps = [":context_proto"],
)

go_proto_library(
    name = "context_go_proto",
    deps = [":context_proto"],
)

proto_library(
    name = "logger_service",
    srcs = ["logger_service.proto"],
    deps = [
        ":log_item_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "logger_service_cc_proto",
    deps = [":logger_service"],
)

cc_grpc_library(
    name = "logger_service_cc_grpc",
    srcs = [":logger_service"],
    grpc_only = True,
    deps = [":logger_service_cc_proto"],
)

py_proto_library(
    name = "logger_service_py_pb2",
    deps = [":logger_service"],
)

py_grpc_library(
    name = "logger_service_py_pb2_grpc",
    srcs = [":logger_service"],
    grpc_library = requirement("grpcio"),
    deps = [":logger_service_py_pb2"],
)

proto_library(
    name = "pubsub_listener_service",
    srcs = ["pubsub_listener_service.proto"],
)

cc_proto_library(
    name = "pubsub_listener_service_cc_proto",
    deps = [":pubsub_listener_service"],
)

cc_grpc_library(
    name = "pubsub_listener_service_cc_grpc",
    srcs = [":pubsub_listener_service"],
    grpc_only = True,
    deps = [":pubsub_listener_service_cc_proto"],
)

py_proto_library(
    name = "pubsub_listener_service_py_pb2",
    deps = [":pubsub_listener_service"],
)

py_grpc_library(
    name = "pubsub_listener_service_py_pb2_grpc",
    srcs = [":pubsub_listener_service"],
    grpc_library = requirement("grpcio"),
    deps = [":pubsub_listener_service_py_pb2"],
)

proto_library(
    name = "log_dispatcher_service",
    srcs = ["log_dispatcher_service.proto"],
    deps = [
        ":blob_proto",
        ":log_item_proto",
        "@com_google_protobuf//:empty_proto",
    ],
)

cc_proto_library(
    name = "log_dispatcher_service_cc_proto",
    deps = [":log_dispatcher_service"],
)

cc_grpc_library(
    name = "log_dispatcher_service_cc_grpc",
    srcs = [":log_dispatcher_service"],
    grpc_only = True,
    deps = [":log_dispatcher_service_cc_proto"],
)

py_proto_library(
    name = "log_dispatcher_service_py_pb2",
    deps = [":log_dispatcher_service"],
)

py_grpc_library(
    name = "log_dispatcher_service_py_pb2_grpc",
    srcs = [":log_dispatcher_service"],
    grpc_library = requirement("grpcio"),
    deps = [":log_dispatcher_service_py_pb2"],
)
