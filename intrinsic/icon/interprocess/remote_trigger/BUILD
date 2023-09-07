# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "binary_futex",
    srcs = ["binary_futex.cc"],
    hdrs = [
        "binary_futex.h",
    ],
    deps = [
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/time",
    ],
)

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
        ":binary_futex",
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/log",
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
        ":binary_futex",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "@com_google_absl//absl/cleanup",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)
