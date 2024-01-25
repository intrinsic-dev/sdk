# Copyright 2023 Intrinsic Innovation LLC

# Client libraries for the ObjectWorldService.

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "frame",
    srcs = ["frame.cc"],
    hdrs = ["frame.h"],
    deps = [
        ":object_world_ids",
        ":transform_node",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
        "//intrinsic/world/proto:object_world_service_cc_proto",
        "@com_google_absl//absl/status:statusor",
    ],
)

cc_library(
    name = "object_entity_filter",
    srcs = ["object_entity_filter.cc"],
    hdrs = ["object_entity_filter.h"],
    deps = [
        ":object_world_ids",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "object_world_ids",
    srcs = ["object_world_ids.cc"],
    hdrs = ["object_world_ids.h"],
    deps = [
        "//intrinsic/util:string_type",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "transform_node",
    srcs = ["transform_node.cc"],
    hdrs = ["transform_node.h"],
    deps = [
        ":object_world_ids",
        "//intrinsic/math:pose3",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
    ],
)

cc_library(
    name = "world_object",
    srcs = ["world_object.cc"],
    hdrs = ["world_object.h"],
    deps = [
        ":frame",
        ":object_entity_filter",
        ":object_world_ids",
        ":transform_node",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
        "//intrinsic/world/proto:object_world_service_cc_proto",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/log:check",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "kinematic_object",
    srcs = ["kinematic_object.cc"],
    hdrs = ["kinematic_object.h"],
    deps = [
        ":frame",
        ":object_world_ids",
        ":transform_node",
        ":world_object",
        "//intrinsic/eigenmath",
        "//intrinsic/icon/proto:cart_space_conversion",
        "//intrinsic/kinematics/types:cartesian_limits",
        "//intrinsic/kinematics/types:joint_limits_xd",
        "//intrinsic/util:eigen",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:object_world_service_cc_proto",
        "@com_google_absl//absl/algorithm:container",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "object_world_client",
    srcs = ["object_world_client.cc"],
    hdrs = ["object_world_client.h"],
    deps = [
        ":frame",
        ":kinematic_object",
        ":object_entity_filter",
        ":object_world_ids",
        ":transform_node",
        ":world_object",
        "//intrinsic/eigenmath",
        "//intrinsic/icon/equipment:equipment_utils",
        "//intrinsic/icon/equipment:icon_equipment_cc_proto",
        "//intrinsic/icon/proto:cart_space_conversion",
        "//intrinsic/kinematics/types:joint_limits_cc_proto",
        "//intrinsic/kinematics/types:joint_limits_xd",
        "//intrinsic/math:pose3",
        "//intrinsic/math:proto_conversion",
        "//intrinsic/math/proto:pose_cc_proto",
        "//intrinsic/resources/proto:resource_handle_cc_proto",
        "//intrinsic/skills/proto:equipment_cc_proto",
        "//intrinsic/util:eigen",
        "//intrinsic/util/status:status_conversion_grpc",
        "//intrinsic/util/status:status_macros",
        "//intrinsic/world/proto:object_world_refs_cc_proto",
        "//intrinsic/world/proto:object_world_service_cc_grpc_proto",
        "//intrinsic/world/proto:object_world_service_cc_proto",
        "//intrinsic/world/proto:object_world_updates_cc_proto",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/log",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "object_world_client_utils",
    srcs = ["object_world_client_utils.cc"],
    hdrs = ["object_world_client_utils.h"],
    deps = [
        ":frame",
        ":object_world_client",
        ":object_world_ids",
        ":transform_node",
        ":world_object",
        "//intrinsic/util/status:status_macros",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)
