# Copyright 2023 Intrinsic Innovation LLC

# Provides the bindings and other utility with externally built zenoh pubsub

cc_library(
    name = "zenoh_handle",
    srcs = ["zenoh_handle.cc"],
    hdrs = ["zenoh_handle.h"],
    data = [
        "//intrinsic/insrc/middleware:libimw_intraprocess_only_asan.so.1",
        "//intrinsic/insrc/middleware:libimw_intraprocess_only_msan.so.1",
        "//intrinsic/insrc/middleware:libimw_intraprocess_only_tsan.so.1",
        "//intrinsic/insrc/middleware:libimw_zenoh.so.1",
    ],
    linkopts = ["-ldl"],  # for dlfcn.h, dlsym in zenoh_handle.cc
    visibility = [
        "//intrinsic/platform/pubsub:__subpackages__",
        "//intrinsic/platform/ros:__subpackages__",
    ],
    deps = [
        ":zenoh_helpers",
        "@bazel_tools//tools/cpp/runfiles",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_test(
    name = "zenoh_handle_test",
    size = "small",
    srcs = ["zenoh_handle_test.cc"],
    deps = [
        ":zenoh_handle",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_library(
    name = "zenoh_helpers",
    srcs = ["zenoh_helpers.cc"],
    hdrs = ["zenoh_helpers.h"],
)

cc_library(
    name = "zenoh_config",
    srcs = ["zenoh_config.cc"],
    hdrs = ["zenoh_config.h"],
    data = [
        ":peer_config.json",
    ],
    visibility = [
        "//intrinsic/platform/pubsub:__subpackages__",
        "//intrinsic/platform/ros:__subpackages__",
    ],
    deps = [
        ":zenoh_helpers",
        "@bazel_tools//tools/cpp/runfiles",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/log",
    ],
)

cc_test(
    name = "zenoh_config_test",
    size = "small",
    srcs = ["zenoh_config_test.cc"],
    deps = [
        ":zenoh_config",
        "@com_google_absl//absl/flags:flag",
        "@com_google_googletest//:gtest_main",
    ],
)
