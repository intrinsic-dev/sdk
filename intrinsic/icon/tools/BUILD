# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_binary(
    name = "disable_motion",
    srcs = ["disable_motion.cc"],
    deprecation = "ICON now auto-enables. Disabling is not meaningful, since ICON will immediately re-enable.",
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "enable_motion",
    srcs = ["enable_motion.cc"],
    deprecation = "ICON now auto-enables. Use this only if you need to clear faults without Flowstate in a pinch. Will be replaced by a pure clear_faults tool soon.",
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "clear_faults",
    srcs = ["clear_faults.cc"],
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/cc_client:operational_status",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "generate_documentation",
    srcs = ["generate_documentation.cc"],
    hdrs = ["generate_documentation.h"],
    deps = [
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "list_actions",
    srcs = ["list_actions.cc"],
    deps = [
        ":generate_documentation",
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "list_parts",
    srcs = ["list_parts.cc"],
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "restart_server",
    srcs = ["restart_server.cc"],
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "show_joint_angles",
    srcs = ["show_joint_angles.cc"],
    deps = [
        "//intrinsic/icon/cc_client:client",
        "//intrinsic/icon/cc_client:operational_status",
        "//intrinsic/icon/proto:part_status_cc_proto",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/time",
    ],
)
