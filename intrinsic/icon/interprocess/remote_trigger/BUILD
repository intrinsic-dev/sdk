# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "remote_trigger_server",
    srcs = [
        "remote_trigger_server.cc",
    ],
    hdrs = [
        "remote_trigger_constants.h",
        "remote_trigger_server.h",
    ],
    deps = [
        "//intrinsic/icon/interprocess:binary_futex",
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/utils:log",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread",
        "//intrinsic/util/thread:thread_options",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "remote_trigger_client",
    srcs = [
        "remote_trigger_client.cc",
    ],
    hdrs = [
        "remote_trigger_client.h",
        "remote_trigger_constants.h",
    ],
    deps = [
        "//intrinsic/icon/interprocess:binary_futex",
        "//intrinsic/icon/interprocess/shared_memory_manager:domain_socket_utils",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)
