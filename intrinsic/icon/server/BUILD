# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "icon_api_service",
    hdrs = ["icon_api_service.h"],
    deps = ["//intrinsic/icon/proto:service_cc_grpc_proto"],
)

cc_library(
    name = "operational_state_interface",
    hdrs = ["operational_state_interface.h"],
    deps = [
        "//intrinsic/icon/cc_client:operational_status",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "grpc_envelope",
    srcs = ["grpc_envelope.cc"],
    hdrs = ["grpc_envelope.h"],
    deps = [
        ":icon_api_service",
        "//intrinsic/hardware/gpio:gpio_service_cc_grpc_proto",
        "//intrinsic/hardware/gpio:gpio_service_cc_proto",
        "//intrinsic/icon/proto:service_cc_grpc_proto",
        "//intrinsic/icon/proto:service_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/icon/utils:exit_code",
        "//intrinsic/icon/utils:realtime_guard",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/util/status:status_macros_grpc",
        "//intrinsic/util/thread",
        "//intrinsic/util/thread:stop_token",
        "@com_github_grpc_grpc//:grpc++",
        "@com_github_grpc_grpc//:grpc_security_base",
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/base:nullability",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:optional",
    ],
)
