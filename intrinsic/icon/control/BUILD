# Copyright 2023 Intrinsic Innovation LLC

package(
    default_visibility = [
        "//visibility:public",
    ],
)

cc_library(
    name = "joint_position_command",
    srcs = ["joint_position_command.cc"],
    hdrs = ["joint_position_command.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:dynamic_limits_check_mode",
    ],
)

cc_library(
    name = "streaming_io_types",
    hdrs = ["streaming_io_types.h"],
    deps = [
        "//intrinsic/util:int_id",
        "@com_google_absl//absl/status:statusor",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "slot_types",
    hdrs = ["slot_types.h"],
    deps = [
        "//intrinsic/icon/proto:types_cc_proto",
        "//intrinsic/util:int_id",
    ],
)

cc_library(
    name = "realtime_clock_interface",
    srcs = ["realtime_clock_interface.cc"],
    hdrs = ["realtime_clock_interface.h"],
    deps = [
        "//intrinsic/icon/utils:core_time",
        "//intrinsic/icon/utils:realtime_status",
        "@com_google_absl//absl/time",
    ],
)
