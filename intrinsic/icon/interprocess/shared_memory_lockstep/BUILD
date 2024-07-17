# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "shared_memory_lockstep",
    srcs = [
        "shared_memory_lockstep.cc",
    ],
    hdrs = [
        "shared_memory_lockstep.h",
    ],
    deps = [
        "//intrinsic/icon/interprocess/shared_memory_manager",
        "//intrinsic/icon/interprocess/shared_memory_manager:memory_segment",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/thread:lockstep",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)
