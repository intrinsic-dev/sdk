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

cc_library(
    name = "realtime_robot_payload",
    srcs = ["realtime_robot_payload.cc"],
    hdrs = ["realtime_robot_payload.h"],
    visibility = ["//intrinsic/icon:__subpackages__"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/utils:fixed_str_cat",
        "//intrinsic/icon/utils:fixed_string",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics:validate_link_parameters",
        "//intrinsic/kinematics/types:to_fixed_string",
        "//intrinsic/math:pose3",
        "//intrinsic/world/proto:robot_payload_cc_proto",
        "//intrinsic/world/robot_payload:robot_payload_base",
    ],
)
