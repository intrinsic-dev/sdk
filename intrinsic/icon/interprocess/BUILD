# Copyright 2023 Intrinsic Innovation LLC

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
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/time",
    ],
)
