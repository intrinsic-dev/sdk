# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = [
    "//visibility:public",
])

exports_files(srcs = [
    "BUILD",
    "robot_payload.cc",
    "robot_payload.h",
    "robot_payload_base.cc",
    "robot_payload_base.h",
])

cc_library(
    name = "robot_payload",
    srcs = ["robot_payload.cc"],
    hdrs = ["robot_payload.h"],
    deps = [
        ":robot_payload_base",
        "//intrinsic/eigenmath",
        "//intrinsic/kinematics:validate_link_parameters",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:robot_payload_cc_proto",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "robot_payload_base",
    srcs = ["robot_payload_base.cc"],
    hdrs = ["robot_payload_base.h"],
    deps = [
        "//intrinsic/eigenmath",
        "//intrinsic/math:pose3",
        "//intrinsic/world/proto:robot_payload_cc_proto",
    ],
)
