# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# This package holds wrappers that make ICON classes available to users of the RTCL C API
# (see parent directory).

package(
    default_visibility = [
        "//visibility:public",
    ],
)

cc_library(
    name = "string_wrapper",
    srcs = ["string_wrapper.cc"],
    hdrs = ["string_wrapper.h"],
    deps = [
        "//intrinsic/icon/control/c_api:icon_c_api",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "streaming_io_wrapper",
    hdrs = ["streaming_io_wrapper.h"],
    deps = [
        ":string_wrapper",
        "//intrinsic/icon/control/c_api:convert_c_realtime_status",
        "//intrinsic/icon/control/c_api:icon_c_api",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)
