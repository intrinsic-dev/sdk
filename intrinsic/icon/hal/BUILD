# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("//bazel:go_macros.bzl", "go_proto_library")
load("//intrinsic/icon/hal/bzl:hardware_module_binary.bzl", "hardware_module_binary")

package(default_visibility = [
    "//visibility:public",
])

proto_library(
    name = "hardware_module_config_proto",
    srcs = ["proto/hardware_module_config.proto"],
    visibility = [
        "//intrinsic:__subpackages__",
    ],
    deps = [
        "//intrinsic/icon/hardware_modules/sim_bus:sim_bus_hardware_module_proto",
        "@com_google_protobuf//:any_proto",
    ],
)

cc_proto_library(
    name = "hardware_module_config_cc_proto",
    deps = [":hardware_module_config_proto"],
)

go_proto_library(
    name = "hardware_module_config_go_proto",
    go_deps = [
        "//intrinsic/icon/hardware_modules/sim_bus:sim_bus_hardware_module_go_proto",
    ],
    deps = [":hardware_module_config_proto"],
)

cc_library(
    name = "hardware_interface_traits",
    hdrs = ["hardware_interface_traits.h"],
)

cc_library(
    name = "hardware_interface_handle",
    hdrs = ["hardware_interface_handle.h"],
    deps = [
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/utils:core_time",
        "@com_github_google_flatbuffers//:flatbuffers",
    ],
)

cc_library(
    name = "hardware_interface_registry",
    srcs = ["hardware_interface_registry.cc"],
    hdrs = [
        "get_hardware_interface.h",
        "hardware_interface_registry.h",
    ],
    deps = [
        ":hardware_interface_handle",
        ":hardware_interface_traits",
        ":hardware_module_config_cc_proto",
        ":module_config",
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/interprocess/shared_memory_manager:segment_info_fbs_cc",
        "//intrinsic/icon/interprocess/shared_memory_manager:segment_info_utils",
        "//intrinsic/icon/release:status_helpers",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "hardware_module_interface",
    hdrs = [
        "hardware_module_interface.h",
    ],
    deps = [
        ":hardware_interface_registry",
        ":module_config",
        "//intrinsic/icon/control:realtime_clock_interface",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "hardware_module_registry",
    hdrs = ["hardware_module_registry.h"],
    deps = [
        ":hardware_module_config_cc_proto",
        ":hardware_module_interface",
    ],
    alwayslink = 1,
)

cc_library(
    name = "hardware_module_runtime",
    srcs = ["hardware_module_runtime.cc"],
    hdrs = [
        "hardware_module_runtime.h",
    ],
    deps = [
        ":hardware_interface_handle",
        ":hardware_interface_registry",
        ":hardware_interface_traits",
        ":hardware_module_config_cc_proto",
        ":hardware_module_interface",
        ":hardware_module_registry",
        "//intrinsic/icon/hal/interfaces:hardware_module_state_fbs_cc",
        "//intrinsic/icon/hal/interfaces:hardware_module_state_fbs_utils",
        "//intrinsic/icon/interprocess/remote_trigger:remote_trigger_server",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:log",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "module_config",
    srcs = ["module_config.cc"],
    hdrs = ["module_config.h"],
    deps = [
        ":hardware_module_config_cc_proto",
        "//intrinsic/icon/control:realtime_clock_interface",
        "//intrinsic/icon/hardware_modules/sim_bus:sim_bus_hardware_module_cc_proto",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/util/proto:any",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
    alwayslink = 1,
)

cc_library(
    name = "realtime_clock",
    srcs = ["realtime_clock.cc"],
    hdrs = [
        "realtime_clock.h",
    ],
    deps = [
        ":hardware_interface_registry",
        "//intrinsic/icon/control:realtime_clock_interface",
        "//intrinsic/icon/interprocess/shared_memory_lockstep",
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:time",
        "//intrinsic/util/thread:lockstep",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

filegroup(
    name = "hardware_module_main",
    srcs = ["hardware_module_main.cc"],
)

cc_library(
    name = "test_module",
    srcs = ["test_module.cc"],
    deps = [
        "//intrinsic/icon/hal:hardware_interface_registry",
        "//intrinsic/icon/hal:hardware_module_interface",
        "//intrinsic/icon/hal:hardware_module_registry",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status",
    ],
    alwayslink = 1,
)

hardware_module_binary(
    name = "hardware_module_main_test",
    hardware_module_lib = ":test_module",
)
