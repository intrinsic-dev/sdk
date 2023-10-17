# Copyright 2023 Intrinsic Innovation LLC

package(
    default_visibility = ["//visibility:public"],
)

cc_library(
    name = "client_utils",
    srcs = ["client_utils.cc"],
    hdrs = ["client_utils.h"],
    deps = [
        ":client",
        ":condition",
        ":robot_config",
        "//intrinsic/icon/common:builtins",
        "//intrinsic/icon/common:part_properties",
        "//intrinsic/icon/release:status_helpers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "state_variable_path",
    srcs = ["state_variable_path.cc"],
    hdrs = [
        "state_variable_path.h",
    ],
    deps = [
        "//intrinsic/icon/common:state_variable_path_constants",
        "//intrinsic/icon/common:state_variable_path_util",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "condition",
    srcs = ["condition.cc"],
    hdrs = ["condition.h"],
    deps = [
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:span",
        "@com_google_absl//absl/types:variant",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "session",
    srcs = ["session.cc"],
    hdrs = ["session.h"],
    deps = [
        ":condition",
        ":stream",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/common:slot_part_map",
        "//intrinsic/icon/proto:concatenate_trajectory_protos",
        "//intrinsic/icon/proto:joint_space_cc_proto",
        "//intrinsic/icon/proto:service_cc_grpc_proto",
        "//intrinsic/icon/proto:service_cc_proto",
        "//intrinsic/icon/proto:streaming_output_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:source_location",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/platform/common/buffers:realtime_write_queue",
        "//intrinsic/util:atomic_sequence_num",
        "//intrinsic/util:int_id",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/grpc:channel_interface",
        "//intrinsic/util/thread",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:optional",
        "@com_google_absl//absl/types:span",
        "@com_google_absl//absl/types:variant",
        "@com_google_googleapis//google/rpc:status_cc_proto",
    ],
)

cc_library(
    name = "client",
    srcs = ["client.cc"],
    hdrs = ["client.h"],
    deps = [
        ":operational_status",
        ":robot_config",
        "//intrinsic/icon/common:part_properties",
        "//intrinsic/icon/common:slot_part_map",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/proto:service_cc_grpc_proto",
        "//intrinsic/icon/proto:service_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:grpc_time_support",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:span",
    ],
)

cc_library(
    name = "operational_status",
    srcs = ["operational_status.cc"],
    hdrs = ["operational_status.h"],
    deps = [
        "//intrinsic/icon/proto:types_cc_proto",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "robot_config",
    srcs = ["robot_config.cc"],
    hdrs = ["robot_config.h"],
    deps = [
        "//intrinsic/icon/proto:generic_part_config_cc_proto",
        "//intrinsic/icon/proto:service_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "stream",
    srcs = ["stream.cc"],
    hdrs = ["stream.h"],
    deps = [
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/proto:service_cc_grpc_proto",
        "//intrinsic/icon/proto:service_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel_interface",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)
