# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "feature_interfaces",
    hdrs = ["feature_interfaces.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/control:joint_position_command",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:cartesian_limits",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/math:pose3",
        "//intrinsic/math:twist",
        "//intrinsic/util:fixed_vector",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:optional",
        "@com_google_absl//absl/types:span",
    ],
)
