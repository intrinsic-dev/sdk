# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "client_common",
    hdrs = ["client_common.h"],
    deps = [
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "equipment_pack",
    srcs = ["equipment_pack.cc"],
    hdrs = ["equipment_pack.h"],
    deps = [
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "skill_canceller",
    srcs = ["skill_canceller.cc"],
    hdrs = ["skill_canceller.h"],
    deps = [
        "//intrinsic/icon/release:status_helpers",
        "@com_google_absl//absl/functional:any_invocable",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
        "@com_google_absl//absl/time",
    ],
)

cc_library(
    name = "skill_interface",
    hdrs = ["skill_interface.h"],
    deps = [
        ":client_common",
        ":equipment_pack",
        ":skill_canceller",
        "//intrinsic/logging/proto:context_cc_proto",
        "//intrinsic/motion_planning:motion_planner_client",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:footprint_cc_proto",
        "//intrinsic/skills/proto:skill_service_cc_proto",
        "//intrinsic/util/proto:any",
        "//intrinsic/world/objects:frame",
        "//intrinsic/world/objects:kinematic_object",
        "//intrinsic/world/objects:object_world_client",
        "//intrinsic/world/objects:world_object",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "skill_registration",
    hdrs = ["skill_registration.h"],
    deps = [
        "//intrinsic/skills/internal:registerer_skill_repository",
    ],
)

cc_library(
    name = "skill_utils",
    srcs = ["skill_utils.cc"],
    hdrs = ["skill_utils.h"],
    deps = [
        "//intrinsic/icon/release:status_helpers",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/skills/proto:skills_cc_proto",
        "//intrinsic/util/grpc:channel",
        "//intrinsic/util/grpc:connection_params",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings:str_format",
    ],
)
