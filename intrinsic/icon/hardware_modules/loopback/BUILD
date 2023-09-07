# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//intrinsic/icon/hal/bzl:hardware_module_binary.bzl", "hardware_module_binary")
load("//intrinsic/icon/hal/bzl:hardware_module_image.bzl", "hardware_module_image")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "loopback_config_proto",
    srcs = ["loopback_config.proto"],
    deps = ["//intrinsic/kinematics/types:joint_limits_proto"],
)

cc_proto_library(
    name = "loopback_config_cc_proto",
    deps = [":loopback_config_proto"],
)

cc_library(
    name = "loopback_hardware_module",
    srcs = ["loopback_hardware_module.cc"],
    hdrs = ["loopback_hardware_module.h"],
    deps = [
        ":loopback_config_cc_proto",
        "//intrinsic/icon/control/safety:safety_messages_fbs_cc",
        "//intrinsic/icon/control/safety:safety_messages_fbs_utils",
        "//intrinsic/icon/hal:hardware_interface_handle",
        "//intrinsic/icon/hal:hardware_interface_registry",
        "//intrinsic/icon/hal:hardware_interface_traits",
        "//intrinsic/icon/hal:hardware_module_interface",
        "//intrinsic/icon/hal:hardware_module_registry",
        "//intrinsic/icon/hal:module_config",
        "//intrinsic/icon/hal/interfaces:joint_command_fbs_cc",
        "//intrinsic/icon/hal/interfaces:joint_command_fbs_utils",
        "//intrinsic/icon/hal/interfaces:joint_limits_fbs_cc",
        "//intrinsic/icon/hal/interfaces:joint_limits_fbs_utils",
        "//intrinsic/icon/hal/interfaces:joint_state_fbs_cc",
        "//intrinsic/icon/hal/interfaces:joint_state_fbs_utils",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:time",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
    alwayslink = 1,
)

hardware_module_binary(
    name = "loopback_hardware_module_main",
    hardware_module_lib = ":loopback_hardware_module",
)

hardware_module_image(
    name = "loopback_hardware_module_image",
    extra_files = [
        "loopback_module_config.pbtxt",
    ],
    hardware_module_binary = "loopback_hardware_module_main",
)

hardware_module_image(
    name = "loopback_hardware_module_generic_image",
    hardware_module_binary = "loopback_hardware_module_main",
)
