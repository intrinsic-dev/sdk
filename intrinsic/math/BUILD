# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "pose3",
    hdrs = [
        "pose3.h",
    ],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:so3",
        "@com_google_absl//absl/base:core_headers",
        "@eigen",
    ],
)

cc_library(
    name = "proto_conversion",
    srcs = ["proto_conversion.cc"],
    hdrs = ["proto_conversion.h"],
    deps = [
        ":pose3",
        "//intrinsic/eigenmath",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/math/proto:point_cc_proto",
        "//intrinsic/math/proto:pose_cc_proto",
        "//intrinsic/math/proto:quaternion_cc_proto",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "twist",
    srcs = ["twist.cc"],
    hdrs = ["twist.h"],
    deps = ["//intrinsic/eigenmath"],
)

cc_library(
    name = "transform_utils",
    srcs = ["transform_utils.cc"],
    hdrs = ["transform_utils.h"],
    deps = [
        ":pose3",
        ":twist",
    ],
)
