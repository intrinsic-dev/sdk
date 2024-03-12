# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "kinematics",
    srcs = [
        "coordinate_frame.cc",
        "elements.cc",
        "joint.cc",
        "link.cc",
    ],
    hdrs = [
        "coordinate_frame.h",
        "elements.h",
        "joint.h",
        "link.h",
    ],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/math:pose3",
        "//intrinsic/third_party/intops:strong_int",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:optional",
        "@com_google_absl//absl/types:span",
    ],
)

cc_library(
    name = "model_interface",
    srcs = [
        "model_interface.cc",
        "model_interface_details.cc",
    ],
    hdrs = [
        "model_interface.h",
        "model_interface_details.h",
    ],
    deps = [
        ":kinematics",
        ":state_values",
        "//intrinsic/eigenmath",
        "//intrinsic/eigenmath:clamp",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/kinematics/types:to_fixed_string",
        "//intrinsic/math:pose3",
        "//intrinsic/util:fixed_vector",
        "//intrinsic/util/status:status_builder",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/container:node_hash_map",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:optional",
        "@com_google_absl//absl/types:span",
    ],
)

cc_library(
    name = "state_values",
    hdrs = ["state_values.h"],
    deps = [
        "//intrinsic/kinematics/types:check_joint_limits",
        "//intrinsic/kinematics/types:joint_limits",
        "//intrinsic/kinematics/types:joint_state",
        "//intrinsic/kinematics/types:to_fixed_string",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "skeleton",
    srcs = ["skeleton.cc"],
    hdrs = ["skeleton.h"],
    deps = [
        ":kinematics",
        ":model_interface",
        "//intrinsic/icon/testing:realtime_annotations",
        "//intrinsic/icon/utils:realtime_status",
        "//intrinsic/icon/utils:realtime_status_macro",
        "//intrinsic/icon/utils:realtime_status_or",
        "//intrinsic/math:pose3",
        "//intrinsic/third_party/intops:strong_int",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/types:optional",
    ],
)
