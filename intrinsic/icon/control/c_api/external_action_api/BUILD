# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "icon_action_interface",
    hdrs = ["icon_action_interface.h"],
    deps = [
        ":icon_action_factory_context",
        ":icon_realtime_slot_map",
        ":icon_streaming_io_access",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "icon_feature_interfaces",
    srcs = ["icon_feature_interfaces.cc"],
    hdrs = ["icon_feature_interfaces.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/control:joint_position_command",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:convert_c_types",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/math:pose3",
        "//intrinsic/math:twist",
    ],
)

cc_library(
    name = "icon_realtime_slot_map",
    srcs = ["icon_realtime_slot_map.cc"],
    hdrs = ["icon_realtime_slot_map.h"],
    deps = [
        ":icon_feature_interfaces",
        "//intrinsic/icon/control:slot_types",
        "//intrinsic/icon/control/c_api:icon_c_api",
    ],
)

cc_library(
    name = "icon_action_factory_context",
    srcs = ["icon_action_factory_context.cc"],
    hdrs = ["icon_action_factory_context.h"],
    deps = [
        "//intrinsic/icon/control:slot_types",
        "//intrinsic/icon/control:streaming_io_types",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/wrappers:streaming_io_wrapper",
        "//intrinsic/icon/control/c_api/wrappers:string_wrapper",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "icon_streaming_io_access",
    hdrs = ["icon_streaming_io_access.h"],
    deps = [
        "//intrinsic/icon/control:streaming_io_types",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/wrappers:streaming_io_wrapper",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
    ],
)

cc_library(
    name = "icon_plugin_register_macro",
    hdrs = ["icon_plugin_register_macro.h"],
    deps = [
        ":make_icon_action_vtable",
        "//intrinsic/icon/control/c_api:icon_c_api",
    ],
)

cc_library(
    name = "make_icon_action_vtable",
    hdrs = ["make_icon_action_vtable.h"],
    deps = [
        ":icon_action_factory_context",
        ":icon_action_interface",
        ":icon_realtime_slot_map",
        ":icon_streaming_io_access",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/wrappers:string_wrapper",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

proto_library(
    name = "sine_wave_action_proto",
    srcs = ["sine_wave_action.proto"],
)

cc_proto_library(
    name = "sine_wave_action_cc_proto",
    deps = [":sine_wave_action_proto"],
)

cc_library(
    name = "sine_wave_plugin_action",
    srcs = ["sine_wave_plugin_action.cc"],
    hdrs = ["sine_wave_plugin_action.h"],
    deps = [
        ":icon_action_interface",
        ":sine_wave_action_cc_proto",
        "//intrinsic/icon/actions:action_utils",
        "//intrinsic/icon/control:slot_types",
        "//intrinsic/icon/control:streaming_io_types",
        "//intrinsic/icon/proto:generic_part_config_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/util:proto_time",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
    alwayslink = True,
)

cc_test(
    name = "sine_wave_plugin_action_test",
    srcs = ["sine_wave_plugin_action_test.cc"],
    deps = [
        ":sine_wave_plugin_action",
        "//intrinsic/icon/control/c_api/external_action_api/testing:action_test_helper",
        "//intrinsic/icon/control/c_api/external_action_api/testing:loopback_fake_arm",
        "//intrinsic/icon/utils:realtime_status_or",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_googletest//:gtest_main",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_binary(
    name = "sine_wave_plugin.so",
    srcs = ["sine_wave_plugin.cc"],
    linkshared = 1,
    linkstatic = 1,
    deps = [
        ":icon_plugin_register_macro",
        ":sine_wave_plugin_action",
    ],
)

cc_binary(
    name = "move_sine_wave",
    srcs = ["move_sine_wave.cc"],
    deps = [
        ":sine_wave_action_cc_proto",
        ":sine_wave_plugin_action",
        "//intrinsic/icon/cc_client:condition",
        "//intrinsic/icon/cc_client:session",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/release/portable:init_xfa_absl",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)
