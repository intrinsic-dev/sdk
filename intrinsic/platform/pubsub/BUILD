# Copyright 2023 Intrinsic Innovation LLC

# Home of pubsub, a non-real-time Publish-Subscribe messaging
# for robotics systems.

load("@bazel_skylib//rules:common_settings.bzl", "string_flag")

package(default_visibility = ["//visibility:public"])

string_flag(
    name = "impl",
    build_setting_default = "zenoh",
    values = [
        "zenoh",
    ],
)

config_setting(
    name = "zenoh_build",
    flag_values = {":impl": "zenoh"},
)

cc_library(
    name = "zenoh_pubsub_data",
    hdrs = ["zenoh_pubsub_data.h"],
)

# PubSub API library. The user-facing API providing access to
# publish-subscribe system.
cc_library(
    name = "pubsub",
    srcs = select({
        ":zenoh_build": [
            "zenoh_pubsub.cc",
        ],
    }),
    hdrs = [
        "pubsub.h",
    ],
    copts = [
        "-fexceptions",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":publisher",
        ":subscription",
        ":zenoh_publisher_data",
        ":zenoh_pubsub_data",
        ":zenoh_subscription_data",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/platform/pubsub/adapters:pubsub_cc_proto",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_config",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_handle",
        "@com_google_absl//absl/base",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/synchronization",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "zenoh_publisher_data",
    hdrs = ["zenoh_publisher_data.h"],
)

cc_library(
    name = "publisher",
    # We need a different publisher implementation also when we move to a
    # different pubsub implementation
    srcs = select({
        ":zenoh_build": ["zenoh_publisher.cc"],
    }),
    hdrs = [
        "publisher.h",
    ],
    copts = [
        "-fexceptions",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":publisher_stats",
        ":zenoh_publisher_data",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/platform/pubsub/adapters:pubsub_cc_proto",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_handle",
        "//intrinsic/util:proto_time",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/strings:str_format",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "zenoh_subscription_data",
    hdrs = ["zenoh_subscription_data.h"],
    deps = [
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_handle",
    ],
)

cc_library(
    name = "subscription",
    # We need a different subscription implementation also when we move to a
    # different pubsub implementation
    srcs = select({
        ":zenoh_build": [
            "zenoh_subscription.cc",
        ],
    }),
    hdrs = [
        "subscription.h",
    ],
    copts = [
        "-fexceptions",
    ],
    features = ["-use_header_modules"],
    deps = [
        ":zenoh_subscription_data",
        "//intrinsic/platform/pubsub/adapters:pubsub_cc_proto",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_handle",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "publisher_stats",
    srcs = ["publisher_stats.cc"],
    hdrs = ["publisher_stats.h"],
    deps = [
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
    ],
)

cc_library(
    name = "zenoh_pubsub",
    srcs = ["zenoh_pubsub.cc"],
    deps = [
        ":publisher",
        ":pubsub",
        ":subscription",
        ":zenoh_publisher_data",
        ":zenoh_pubsub_data",
        ":zenoh_subscription_data",
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_config",
        "//intrinsic/platform/pubsub/zenoh_util:zenoh_handle",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/strings:str_format",
    ],
)
