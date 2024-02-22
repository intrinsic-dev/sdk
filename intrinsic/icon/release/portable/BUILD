# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "init_xfa_absl",
    srcs = ["init_xfa_absl.cc"],
    hdrs = ["init_xfa.h"],
    deps = [
        "//intrinsic/icon/utils:log",
        "@com_google_absl//absl/flags:parse",
        "@com_google_absl//absl/flags:usage",
    ],
)

cc_test(
    name = "init_xfa_absl_test",
    srcs = ["init_xfa_test.cc"],
    deps = [
        ":init_xfa_absl",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/flags:flag",
        "@com_google_absl//absl/strings",
    ],
)
