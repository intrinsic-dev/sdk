# Copyright 2023 Intrinsic Innovation LLC

# PubSub adapters implementations.

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "pubsub_proto",
    srcs = ["pubsub.proto"],
    deps = [
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "pubsub_cc_proto",
    deps = [":pubsub_proto"],
)
