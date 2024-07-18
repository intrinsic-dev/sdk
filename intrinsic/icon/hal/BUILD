# Copyright 2023 Intrinsic Innovation LLC

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
        ":icon_state_register",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_cc",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:current_cycle",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
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
        ":icon_state_register",
        ":module_config",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_cc",
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/interprocess/shared_memory_manager:segment_info_fbs_cc",
        "//intrinsic/icon/interprocess/shared_memory_manager:segment_info_utils",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/util/status:status_macros",
        "@com_github_google_flatbuffers//:flatbuffers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "hardware_module_init_context",
    hdrs = [
        "hardware_module_init_context.h",
    ],
    deps = [
        ":hardware_interface_registry",
        ":module_config",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/base:core_headers",
    ],
)

cc_library(
    name = "hardware_module_interface",
    hdrs = [
        "hardware_module_interface.h",
    ],
    deps = [
        ":hardware_module_init_context",
        ":module_config",
        "//intrinsic/icon/control:realtime_clock_interface",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "icon_state_register",
    hdrs = ["icon_state_register.h"],
    deps = [
        ":hardware_interface_traits",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_cc",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_utils",
        "@com_google_absl//absl/strings:string_view",
    ],
)

cc_library(
    name = "command_validator",
    srcs = ["command_validator.cc"],
    hdrs = [
        "command_validator.h",
    ],
    deps = [
        ":hardware_interface_handle",
        ":hardware_interface_registry",
        ":icon_state_register",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_cc",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:string_view",
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
    name = "hardware_module_util",
    srcs = ["hardware_module_util.cc"],
    hdrs = [
        "hardware_module_util.h",
    ],
    deps = [
        "//intrinsic/icon/hal/interfaces:hardware_module_state_fbs_cc",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
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
        ":hardware_module_init_context",
        ":hardware_module_interface",
        ":hardware_module_registry",
        ":hardware_module_util",
        ":icon_state_register",
        "//intrinsic/icon/hal/interfaces:hardware_module_state_fbs_cc",
        "//intrinsic/icon/hal/interfaces:hardware_module_state_fbs_utils",
        "//intrinsic/icon/hal/interfaces:icon_state_fbs_cc",
        "//intrinsic/icon/interprocess/remote_trigger:remote_trigger_server",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:async_buffer",
        "//intrinsic/icon/utils:async_request",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:fixed_string",
        "//intrinsic/icon/utils:log",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/platform/common/buffers:rt_promise",
        "//intrinsic/platform/common/buffers:rt_queue",
        "//intrinsic/platform/common/buffers:rt_queue_multi_writer",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread",
        "//intrinsic/util/thread:thread_options",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/base:core_headers",
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
        "//intrinsic/util/thread:thread_options",
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
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:time",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread:lockstep",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
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
        ":hardware_module_init_context",
        ":hardware_module_interface",
        ":hardware_module_registry",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/status",
    ],
    alwayslink = 1,
)

cc_library(
    name = "hardware_module_main_util",
    srcs = ["hardware_module_main_util.cc"],
    hdrs = ["hardware_module_main_util.h"],
    deps = [
        ":hardware_module_config_cc_proto",
        ":hardware_module_registry",
        ":hardware_module_runtime",
        ":hardware_module_util",
        ":module_config",
        ":realtime_clock",
        "//intrinsic/icon/release:file_helpers",
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:shutdown_signals",
        "//intrinsic/icon/utils:time",
        "//intrinsic/resources/proto:resource_registry_cc_proto",
        "//intrinsic/resources/proto:runtime_context_cc_proto",
        "//intrinsic/util/proto:any",
        "//intrinsic/util/proto:get_text_proto",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread",
        "//intrinsic/util/thread:thread_options",
        "//intrinsic/util/thread:util",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc_security_base",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

hardware_module_binary(
    name = "hardware_module_main_test",
    hardware_module_lib = ":test_module",
)
