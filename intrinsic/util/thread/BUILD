# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "thread_options",
    srcs = ["thread_options.cc"],
    hdrs = ["thread_options.h"],
    deps = ["@com_google_absl//absl/strings"],
)

cc_library(
    name = "thread_utils",
    srcs = [
        "thread_utils.cc",
    ],
    hdrs = [
        "thread_utils.h",
    ],
    copts = ["-D_GNU_SOURCE"],
    deps = [
        ":thread_options",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:log",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/functional:any_invocable",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
    ],
)

cc_library(
    name = "thread",
    srcs = ["thread.cc"],
    hdrs = ["thread.h"],
    deps = [
        ":thread_options",
        ":thread_utils",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/functional:bind_front",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "stop_token",
    hdrs = ["stop_token.h"],
    deps = [
        "@com_google_absl//absl/base:core_headers",
    ],
)

cc_library(
    name = "lockstep",
    srcs = ["lockstep.cc"],
    hdrs = ["lockstep.h"],
    deps = [
        "//intrinsic/icon/interprocess:binary_futex",
        "//intrinsic/icon/utils:log",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "util",
    srcs = ["util.cc"],
    hdrs = ["util.h"],
    deps = [
        "//intrinsic/util/status:status_macros",
        "@com_github_google_re2//:re2",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/functional:any_invocable",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)
