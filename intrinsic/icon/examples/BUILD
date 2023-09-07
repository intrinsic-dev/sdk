# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "adio_lib",
    srcs = ["adio_lib.cc"],
    hdrs = ["adio_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/icon/actions:adio_cc_proto",
        "//intrinsic/icon/actions:adio_info",
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:span",
    ],
)

cc_binary(
    name = "adio",
    srcs = ["adio.cc"],
    deps = [
        ":adio_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

proto_library(
    name = "joint_move_positions_proto",
    srcs = ["joint_move_positions.proto"],
)

cc_proto_library(
    name = "joint_move_positions_cc_proto",
    deps = [":joint_move_positions_proto"],
)

cc_library(
    name = "joint_move_lib",
    srcs = ["joint_move_lib.cc"],
    hdrs = ["joint_move_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/icon/actions:point_to_point_move_info",
        "//intrinsic/icon/cc_client:client_utils",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:builtins",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "joint_move",
    srcs = ["joint_move.cc"],
    deps = [
        ":joint_move_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "joint_then_cart_move_lib",
    srcs = ["joint_then_cart_move_lib.cc"],
    hdrs = ["joint_then_cart_move_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/actions:cartesian_position_info",
        "//intrinsic/icon/actions:point_to_point_move_info",
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/cc_client:client_utils",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:builtins",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/proto:cart_space_cc_proto",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)

cc_binary(
    name = "joint_then_cart_move",
    srcs = ["joint_then_cart_move.cc"],
    deps = [
        ":joint_then_cart_move_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "blended_joint_move_lib",
    srcs = ["blended_joint_move_lib.cc"],
    hdrs = ["blended_joint_move_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/actions:blended_move_action_info",
        "//intrinsic/icon/actions:point_to_point_move_info",
        "//intrinsic/icon/cc_client:client_utils",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:builtins",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/motion_planning/trajectory_planning:blended_joint_move_cc_proto",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "blended_joint_move",
    srcs = ["blended_joint_move.cc"],
    deps = [
        ":blended_joint_move_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "blended_cartesian_move_lib",
    srcs = ["blended_cartesian_move_lib.cc"],
    hdrs = ["blended_cartesian_move_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:rotation_utils",
        "//intrinsic/icon/actions:blended_move_action_info",
        "//intrinsic/icon/actions:point_to_point_move_info",
        "//intrinsic/icon/cc_client:client_utils",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:builtins",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/proto:blended_cartesian_move_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/motion_planning/trajectory_planning:blended_joint_move_cc_proto",
        "//intrinsic/util:proto_time",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:span",
    ],
)

cc_binary(
    name = "blended_cartesian_move",
    srcs = ["blended_cartesian_move.cc"],
    deps = [
        ":blended_cartesian_move_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "introspection",
    srcs = ["introspection.cc"],
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/proto:cart_space_cc_proto",
        "//intrinsic/icon/proto:io_block_cc_proto",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)

cc_library(
    name = "joint_move_loop_lib",
    srcs = ["joint_move_loop_lib.cc"],
    hdrs = ["joint_move_loop_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        ":joint_move_positions_cc_proto",
        "//intrinsic/icon/actions:point_to_point_move_info",
        "//intrinsic/icon/cc_client:client_utils",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util:eigen",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

cc_binary(
    name = "joint_move_loop",
    srcs = ["joint_move_loop.cc"],
    deps = [
        ":joint_move_loop_lib",
        ":joint_move_positions_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/proto:get_text_proto",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "simple_gripper_lib",
    srcs = ["simple_gripper_lib.cc"],
    hdrs = ["simple_gripper_lib.h"],
    visibility = ["//visibility:private"],
    deps = [
        "//intrinsic/icon/actions:simple_gripper_cc_proto",
        "//intrinsic/icon/actions:simple_gripper_info",
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/grpc:channel_interface",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:span",
    ],
)

cc_binary(
    name = "simple_gripper",
    srcs = ["simple_gripper.cc"],
    deps = [
        ":simple_gripper_lib",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)
