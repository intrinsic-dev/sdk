# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "icon_action_factory_context_fake",
    testonly = True,
    srcs = ["icon_action_factory_context_fake.cc"],
    hdrs = ["icon_action_factory_context_fake.h"],
    deps = [
        ":icon_slot_map_fake",
        ":icon_streaming_io_registry_fake",
        "//intrinsic/icon/control:streaming_io_types",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/external_action_api:icon_action_factory_context",
        "//intrinsic/icon/control/c_api/wrappers:string_wrapper",
        "//intrinsic/icon/proto:types_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "icon_streaming_io_registry_fake",
    testonly = True,
    srcs = ["icon_streaming_io_registry_fake.cc"],
    hdrs = ["icon_streaming_io_registry_fake.h"],
    deps = [
        "//intrinsic/icon/control:streaming_io_types",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/external_action_api:icon_streaming_io_access",
        "//intrinsic/icon/control/c_api/wrappers:streaming_io_wrapper",
        "//intrinsic/icon/control/c_api/wrappers:string_wrapper",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:realtime_status_or",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "loopback_fake_arm",
    testonly = True,
    srcs = ["loopback_fake_arm.cc"],
    hdrs = ["loopback_fake_arm.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:rotation_utils",
        "//intrinsic/icon/control:joint_position_command",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:convert_c_types",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/proto:generic_part_config_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_limits_cc_proto",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/math:pose3",
        "//intrinsic/math:twist",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "icon_slot_map_fake",
    testonly = True,
    srcs = ["icon_slot_map_fake.cc"],
    hdrs = ["icon_slot_map_fake.h"],
    deps = [
        ":loopback_fake_arm",
        "//intrinsic/icon/control:slot_types",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/control/c_api/external_action_api:icon_realtime_slot_map",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/kinematics/types:joint_limits",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "action_test_helper",
    testonly = True,
    srcs = ["action_test_helper.cc"],
    hdrs = ["action_test_helper.h"],
    deps = [
        ":icon_action_factory_context_fake",
        ":icon_slot_map_fake",
        ":icon_streaming_io_registry_fake",
        "//intrinsic/icon/control/c_api/external_action_api:icon_action_interface",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)
