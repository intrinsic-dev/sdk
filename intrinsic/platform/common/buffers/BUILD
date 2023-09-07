# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Specialized Buffer Implementations

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "rt_queue",
    hdrs = ["rt_queue.h"],
    deps = [
        ":rt_queue_buffer",
        "//intrinsic/icon/utils:realtime_guard",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/types:optional",
    ],
)

cc_library(
    name = "realtime_write_queue",
    srcs = ["realtime_write_queue.cc"],
    hdrs = ["realtime_write_queue.h"],
    deps = [
        ":rt_queue_buffer",
        "//intrinsic/platform/common/buffers/internal:event_fd",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:optional",
    ],
)

cc_library(
    name = "rt_queue_buffer",
    hdrs = ["rt_queue_buffer.h"],
    visibility = ["//visibility:private"],
    deps = [
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/functional:function_ref",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/memory",
        "@com_google_absl//absl/types:optional",
    ],
)
