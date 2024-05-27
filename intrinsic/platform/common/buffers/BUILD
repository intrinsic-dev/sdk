# Copyright 2023 Intrinsic Innovation LLC

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
        "@com_google_absl//absl/log:check",
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

cc_library(
    name = "rt_promise",
    hdrs = ["rt_promise.h"],
    deps = [
        ":rt_queue_buffer",
        "//intrinsic/icon/interprocess:binary_futex",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:log",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "rt_queue_multi_writer",
    hdrs = ["rt_queue_multi_writer.h"],
    deps = [
        ":rt_queue",
        "//intrinsic/icon/utils:realtime_guard",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/synchronization",
    ],
)

cc_test(
    name = "rt_queue_multi_writer_test",
    srcs = ["rt_queue_multi_writer_test.cc"],
    deps = [
        ":rt_queue",
        ":rt_queue_multi_writer",
        "//intrinsic/util/testing:gtest_wrapper",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/status",
    ],
)
