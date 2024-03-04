# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "constants",
    hdrs = ["constants.h"],
    deps = [
        "//intrinsic/eigenmath",
    ],
)

cc_library(
    name = "fixed_string",
    hdrs = ["fixed_string.h"],
    deps = [
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "fixed_str_cat",
    hdrs = ["fixed_str_cat.h"],
    deps = [
        ":fixed_string",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "realtime_status",
    srcs = ["realtime_status.cc"],
    hdrs = ["realtime_status.h"],
    deps = [
        ":fixed_str_cat",
        ":fixed_string",
        ":realtime_guard",
        "//intrinsic/icon/testing:realtime_annotations",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "realtime_status_or",
    hdrs = ["realtime_status_or.h"],
    deps = [
        ":realtime_status",
        "//intrinsic/icon/testing:realtime_annotations",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "realtime_status_macro",
    hdrs = ["realtime_status_macro.h"],
    deps = [
        ":fixed_str_cat",
        ":realtime_status",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/base:core_headers",
    ],
)

cc_library(
    name = "core_time",
    srcs = [
        "clock.cc",
    ],
    hdrs = [
        "clock.h",
    ],
    deps = [
        ":log_internal",
        ":time",
        "//intrinsic/icon/testing:realtime_annotations",
        "@com_google_absl//absl/log:check",
    ],
)

cc_library(
    name = "time",
    srcs = [
        "duration.cc",
    ],
    hdrs = [
        "clock_base.h",
        "duration.h",
    ],
    deps = [
        "@com_google_absl//absl/base:core_headers",
    ],
)

cc_library(
    name = "realtime_log_sink",
    srcs = ["realtime_log_sink.cc"],
    hdrs = ["realtime_log_sink.h"],
    deps = [
        ":log_sink",
        ":realtime_guard",
        "//intrinsic/icon/interprocess:binary_futex",
        "//intrinsic/platform/common/buffers:realtime_write_queue",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "log_internal",
    srcs = ["log_internal.cc"],
    hdrs = ["log_internal.h"],
    visibility = [
        "//visibility:private",  # Only private by automation, not intent. Owner may accept CLs adding visibility. See go/scheuklappen#explicit-private.
    ],
    deps = [
        ":fixed_string",
        ":log_sink",
        "//intrinsic/icon/release:source_location",
        "//intrinsic/icon/testing:realtime_annotations",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "log",
    srcs = ["log.cc"],
    hdrs = ["log.h"],
    deps = [
        ":log_internal",
        ":log_sink",
        ":realtime_log_sink",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/log",
    ],
)

cc_test(
    name = "log_test",
    srcs = ["log_test.cc"],
    deps = [
        ":log",
        ":log_internal",
        "//intrinsic/icon/release:source_location",
        "//intrinsic/util/testing:gtest_wrapper",
        "//intrinsic/util/thread",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "log_sink",
    srcs = ["log_sink.cc"],
    hdrs = ["log_sink.h"],
    deps = [
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "realtime_guard",
    srcs = [
        "log.h",  # Avoid circular dep realtime_guard <-> realtime_log_sink.
        "realtime_guard.cc",
    ],
    hdrs = [
        "realtime_guard.h",
    ],
    linkopts = [
        "-ldl",  # for dlfcn.h, dladdr in realtime_guard.cc
    ],
    deps = [
        ":log_internal",
        ":log_sink",
        "//intrinsic/icon/release:source_location",
        "@com_google_absl//absl/base:log_severity",
        "@com_google_absl//absl/debugging:stacktrace",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/strings",
    ],
)

cc_test(
    name = "realtime_guard_test",
    srcs = [
        "realtime_guard_test.cc",
    ],
    deps = [
        ":log",
        ":log_sink",
        ":realtime_guard",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/types:span",
    ],
)

cc_library(
    name = "current_cycle",
    hdrs = ["current_cycle.h"],
)
