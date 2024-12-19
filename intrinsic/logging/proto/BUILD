# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:cc_grpc_library.bzl", "cc_grpc_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")
load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("//bazel:go_macros.bzl", "go_grpc_library", "go_proto_library")

package(default_visibility = ["//visibility:public"])

proto_library(
    name = "log_item_proto",
    srcs = ["log_item.proto"],
    deps = [
        ":blob_proto",
        ":context_proto",
        ":critical_event_log",
        ":flowstate_event",
        "//intrinsic/executive/proto:log_items_proto",
        "//intrinsic/icon/proto:cart_space_proto",
        "//intrinsic/icon/proto:joint_space_proto",
        "//intrinsic/icon/proto:part_status_proto",
        "//intrinsic/logging/errors/proto:error_report_proto",
        "//intrinsic/perception/proto:frame_proto",
        "//intrinsic/perception/proto:hand_eye_calibration",
        "//intrinsic/perception/proto:pose_estimation_result",
        "//intrinsic/skills/proto:skill_service_proto",
        "//intrinsic/util/status:extended_status_proto",
        "@com_google_protobuf//:any_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "log_item_cc_proto",
    deps = [":log_item_proto"],
)

go_proto_library(
    name = "log_item_go_proto",
    go_deps = [
        ":blob_go_proto",
        ":context_go_proto",
        ":bag_metadata_go_proto",
        ":critical_event_log_go_proto",
        ":flowstate_event_go_proto",
        "//intrinsic/executive/proto:log_items_go_proto",
        "//intrinsic/icon/proto:cart_space_go_proto",
        "//intrinsic/icon/proto:joint_space_go_proto",
        "//intrinsic/icon/proto:io_block_go_proto",
        "//intrinsic/icon/proto:safety_status_go_proto",
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:quaternion_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
        "//intrinsic/kinematics/proto:kinematics_go_proto",
        "//intrinsic/kinematics/proto:skeleton_go_proto",
        "//intrinsic/kinematics/types:joint_limits_go_proto",
        "//intrinsic/icon/proto:generic_part_config_go_proto",
        "//intrinsic/icon/proto:types_go_proto",
        "//intrinsic/math/proto:vector3_go_proto",
        "//intrinsic/icon/proto:part_status_go_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "//intrinsic/logging/errors/proto:error_report_go_proto",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_go_proto",
        "//intrinsic/hardware/gpio:signal_go_proto",
        "//intrinsic/hardware/gripper/eoat:gripper_config_go_proto",
        "//intrinsic/hardware/gripper/eoat:eoat_service_go_proto",
        "//intrinsic/hardware/proto:settings_go_proto",
        "//intrinsic/kinematics/types:dynamic_limits_check_mode_go_proto",
        "//intrinsic/skills/proto:skill_parameter_metadata_go_proto",
        "//intrinsic/perception/proto:pose_estimate_in_root_go_proto",
        "//intrinsic/world/proto:object_world_refs_go_proto",
        "//intrinsic/world/proto:collision_action_go_proto",
        "//intrinsic/world/proto:collision_settings_go_proto",
        "//intrinsic/math/proto:vector2_go_proto",
        "//intrinsic/geometry/proto:axis_aligned_bounding_box_go_proto",
        "//intrinsic/geometry/proto:oriented_bounding_box_go_proto",
        "//intrinsic/math/proto:array_go_proto",
        "//intrinsic/math/proto:twist_go_proto",
        "//intrinsic/perception/proto:distortion_params_go_proto",
        "//intrinsic/perception/proto:dimensions_go_proto",
        "//intrinsic/perception/proto:intrinsic_params_go_proto",
        "//intrinsic/perception/proto:camera_params_go_proto",
        "//intrinsic/perception/proto:image_buffer_go_proto",
        "//intrinsic/geometry/service:geometry_storage_refs_go_proto",
        "//intrinsic/geometry/service:transformed_geometry_storage_refs_go_proto",
        "//intrinsic/geometry/proto:octree_go_proto",
        "//intrinsic/geometry/proto:mesh_octree_wrapping_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/geometry/proto:triangle_mesh_go_proto",
        "//intrinsic/geometry/proto:lazy_exact_geometry_go_proto",
        "//intrinsic/world/proto:geometry_component_go_proto",
        "//intrinsic/world/proto:gripper_component_go_proto",
        "//intrinsic/perception/proto:frame_go_proto",
        "//intrinsic/perception/proto:vector_go_proto",
        "//intrinsic/perception/proto:pattern_detection_result_go_proto",
        "//intrinsic/perception/proto:intrinsic_calibration_go_proto",
        "//intrinsic/perception/proto:hand_eye_calibration_go_proto",
        "//intrinsic/perception/proto:camera_drivers_go_proto",
        "//intrinsic/perception/proto:camera_identifier_go_proto",
        "//intrinsic/perception/proto:camera_settings_go_proto",
        "//intrinsic/perception/proto:sensor_config_go_proto",
        "//intrinsic/perception/proto:camera_config_go_proto",
        "//intrinsic/math/proto:affine_go_proto",
        "//intrinsic/perception/proto:pose_estimation_result_go_proto",
        "//intrinsic/scene/proto/v1:entity_go_proto",
        "//intrinsic/scene/proto/v1:object_properties_go_proto",
        "//intrinsic/scene/proto/v1:simulation_spec_go_proto",
        "//intrinsic/skills/proto:error_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/skills/proto:footprint_go_proto",
        "//intrinsic/geometry/proto:renderable_go_proto",
        "//intrinsic/geometry/proto:geometry_go_proto",
        "//intrinsic/geometry/service:geometry_service_types_go_proto",
        "//intrinsic/world/proto:object_world_updates_go_proto",
        "//intrinsic/skills/proto:prediction_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
        "//intrinsic/skills/proto:equipment_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/skills/proto:skill_service_go_grpc_proto",
    ],
    deps = [":log_item_proto"],
)

py_proto_library(
    name = "log_item_py_pb2",
    deps = [":log_item_proto"],
)

proto_library(
    name = "blob_proto",
    srcs = ["blob.proto"],
)

cc_proto_library(
    name = "blob_cc_proto",
    deps = [":blob_proto"],
)

go_proto_library(
    name = "blob_go_proto",
    deps = [":blob_proto"],
)

py_proto_library(
    name = "blob_py_pb2",
    deps = [":blob_proto"],
)

proto_library(
    name = "context_proto",
    srcs = ["context.proto"],
)

proto_library(
    name = "critical_event_log",
    srcs = ["critical_event_log.proto"],
)

cc_proto_library(
    name = "critical_event_log_cc_proto",
    deps = [":critical_event_log"],
)

py_proto_library(
    name = "critical_event_log_py_pb2",
    deps = [":critical_event_log"],
)

go_proto_library(
    name = "critical_event_log_go_proto",
    deps = [":critical_event_log"],
)

proto_library(
    name = "flowstate_event",
    srcs = ["flowstate_event.proto"],
    visibility = ["//visibility:private"],
)

cc_proto_library(
    name = "flowstate_event_cc_proto",
    deps = [":flowstate_event"],
)

go_proto_library(
    name = "flowstate_event_go_proto",
    deps = [":flowstate_event"],
)

py_proto_library(
    name = "flowstate_event_py_pb2",
    deps = [":flowstate_event"],
)

py_proto_library(
    name = "context_py_pb2",
    deps = [":context_proto"],
)

cc_proto_library(
    name = "context_cc_proto",
    deps = [":context_proto"],
)

go_proto_library(
    name = "context_go_proto",
    visibility = ["//intrinsic:__subpackages__"],
    deps = [":context_proto"],
)

proto_library(
    name = "logger_service",
    srcs = ["logger_service.proto"],
    deps = [
        ":bag_metadata_proto",
        ":log_item_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "logger_service_cc_proto",
    deps = [":logger_service"],
)

cc_grpc_library(
    name = "logger_service_cc_grpc",
    srcs = [":logger_service"],
    grpc_only = True,
    deps = [":logger_service_cc_proto"],
)

py_proto_library(
    name = "logger_service_py_pb2",
    deps = [":logger_service"],
)

py_grpc_library(
    name = "logger_service_py_pb2_grpc",
    srcs = [":logger_service"],
    grpc_library = requirement("grpcio"),
    deps = [":logger_service_py_pb2"],
)

go_proto_library(
    name = "logger_service_go_proto",
    go_deps = [
        ":blob_go_proto",
        ":context_go_proto",
        ":bag_metadata_go_proto",
        ":critical_event_log_go_proto",
        ":flowstate_event_go_proto",
        "//intrinsic/executive/proto:log_items_go_proto",
        "//intrinsic/icon/proto:cart_space_go_proto",
        "//intrinsic/icon/proto:joint_space_go_proto",
        "//intrinsic/icon/proto:io_block_go_proto",
        "//intrinsic/icon/proto:safety_status_go_proto",
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:quaternion_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
        "//intrinsic/kinematics/proto:kinematics_go_proto",
        "//intrinsic/kinematics/proto:skeleton_go_proto",
        "//intrinsic/kinematics/types:joint_limits_go_proto",
        "//intrinsic/icon/proto:generic_part_config_go_proto",
        "//intrinsic/icon/proto:types_go_proto",
        "//intrinsic/math/proto:vector3_go_proto",
        "//intrinsic/icon/proto:part_status_go_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "//intrinsic/logging/errors/proto:error_report_go_proto",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_go_proto",
        "//intrinsic/hardware/gpio:signal_go_proto",
        "//intrinsic/hardware/gripper/eoat:gripper_config_go_proto",
        "//intrinsic/hardware/gripper/eoat:eoat_service_go_proto",
        "//intrinsic/hardware/proto:settings_go_proto",
        "//intrinsic/kinematics/types:dynamic_limits_check_mode_go_proto",
        "//intrinsic/skills/proto:skill_parameter_metadata_go_proto",
        "//intrinsic/perception/proto:pose_estimate_in_root_go_proto",
        "//intrinsic/world/proto:object_world_refs_go_proto",
        "//intrinsic/world/proto:collision_action_go_proto",
        "//intrinsic/world/proto:collision_settings_go_proto",
        "//intrinsic/math/proto:vector2_go_proto",
        "//intrinsic/geometry/proto:axis_aligned_bounding_box_go_proto",
        "//intrinsic/geometry/proto:oriented_bounding_box_go_proto",
        "//intrinsic/math/proto:array_go_proto",
        "//intrinsic/math/proto:twist_go_proto",
        "//intrinsic/perception/proto:distortion_params_go_proto",
        "//intrinsic/perception/proto:dimensions_go_proto",
        "//intrinsic/perception/proto:intrinsic_params_go_proto",
        "//intrinsic/perception/proto:camera_params_go_proto",
        "//intrinsic/perception/proto:image_buffer_go_proto",
        "//intrinsic/geometry/service:geometry_storage_refs_go_proto",
        "//intrinsic/geometry/service:transformed_geometry_storage_refs_go_proto",
        "//intrinsic/geometry/proto:octree_go_proto",
        "//intrinsic/geometry/proto:mesh_octree_wrapping_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/geometry/proto:triangle_mesh_go_proto",
        "//intrinsic/geometry/proto:lazy_exact_geometry_go_proto",
        "//intrinsic/world/proto:geometry_component_go_proto",
        "//intrinsic/world/proto:gripper_component_go_proto",
        "//intrinsic/perception/proto:frame_go_proto",
        "//intrinsic/perception/proto:vector_go_proto",
        "//intrinsic/perception/proto:pattern_detection_result_go_proto",
        "//intrinsic/perception/proto:intrinsic_calibration_go_proto",
        "//intrinsic/perception/proto:hand_eye_calibration_go_proto",
        "//intrinsic/perception/proto:camera_drivers_go_proto",
        "//intrinsic/perception/proto:camera_identifier_go_proto",
        "//intrinsic/perception/proto:camera_settings_go_proto",
        "//intrinsic/perception/proto:sensor_config_go_proto",
        "//intrinsic/perception/proto:camera_config_go_proto",
        "//intrinsic/math/proto:affine_go_proto",
        "//intrinsic/perception/proto:pose_estimation_result_go_proto",
        "//intrinsic/scene/proto/v1:entity_go_proto",
        "//intrinsic/skills/proto:error_go_proto",
        "//intrinsic/scene/proto/v1:object_properties_go_proto",
        "//intrinsic/scene/proto/v1:simulation_spec_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/skills/proto:footprint_go_proto",
        "//intrinsic/geometry/proto:renderable_go_proto",
        "//intrinsic/geometry/proto:geometry_go_proto",
        "//intrinsic/geometry/service:geometry_service_types_go_proto",
        "//intrinsic/world/proto:object_world_updates_go_proto",
        "//intrinsic/skills/proto:prediction_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
        "//intrinsic/skills/proto:equipment_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/skills/proto:skill_service_go_grpc_proto",
        "//intrinsic/logging/proto:log_item_go_proto",
    ],
    deps = [":logger_service"],
)

go_grpc_library(
    name = "logger_service_go_grpc_proto",
    srcs = [":logger_service"],
    deps = [
        ":bag_metadata_go_proto",
        ":blob_go_proto",
        ":context_go_proto",
        ":critical_event_log_go_proto",
        ":flowstate_event_go_proto",
        ":log_item_go_proto",
        ":logger_service_go_proto",
        "//intrinsic/executive/proto:log_items_go_proto",
    ],
)

proto_library(
    name = "pubsub_listener_service",
    srcs = ["pubsub_listener_service.proto"],
)

cc_proto_library(
    name = "pubsub_listener_service_cc_proto",
    deps = [":pubsub_listener_service"],
)

cc_grpc_library(
    name = "pubsub_listener_service_cc_grpc",
    srcs = [":pubsub_listener_service"],
    grpc_only = True,
    deps = [":pubsub_listener_service_cc_proto"],
)

py_proto_library(
    name = "pubsub_listener_service_py_pb2",
    deps = [":pubsub_listener_service"],
)

py_grpc_library(
    name = "pubsub_listener_service_py_pb2_grpc",
    srcs = [":pubsub_listener_service"],
    grpc_library = requirement("grpcio"),
    deps = [":pubsub_listener_service_py_pb2"],
)

proto_library(
    name = "log_dispatcher_service",
    srcs = ["log_dispatcher_service.proto"],
    deps = [
        ":blob_proto",
        ":log_item_proto",
        "@com_google_protobuf//:empty_proto",
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "log_dispatcher_service_cc_proto",
    deps = [":log_dispatcher_service"],
)

cc_grpc_library(
    name = "log_dispatcher_service_cc_grpc",
    srcs = [":log_dispatcher_service"],
    grpc_only = True,
    deps = [":log_dispatcher_service_cc_proto"],
)

py_proto_library(
    name = "log_dispatcher_service_py_pb2",
    deps = [":log_dispatcher_service"],
)

py_grpc_library(
    name = "log_dispatcher_service_py_pb2_grpc",
    srcs = [":log_dispatcher_service"],
    grpc_library = requirement("grpcio"),
    deps = [":log_dispatcher_service_py_pb2"],
)

go_proto_library(
    name = "log_dispatcher_service_go_proto",
    go_deps = [
        ":blob_go_proto",
        ":context_go_proto",
        ":bag_metadata_go_proto",
        ":critical_event_log_go_proto",
        ":flowstate_event_go_proto",
        "//intrinsic/executive/proto:log_items_go_proto",
        "//intrinsic/icon/proto:cart_space_go_proto",
        "//intrinsic/icon/proto:joint_space_go_proto",
        "//intrinsic/icon/proto:io_block_go_proto",
        "//intrinsic/icon/proto:safety_status_go_proto",
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:quaternion_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
        "//intrinsic/kinematics/proto:kinematics_go_proto",
        "//intrinsic/kinematics/proto:skeleton_go_proto",
        "//intrinsic/kinematics/types:joint_limits_go_proto",
        "//intrinsic/icon/proto:generic_part_config_go_proto",
        "//intrinsic/icon/proto:types_go_proto",
        "//intrinsic/math/proto:vector3_go_proto",
        "//intrinsic/icon/proto:part_status_go_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "//intrinsic/logging/errors/proto:error_report_go_proto",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_go_proto",
        "//intrinsic/hardware/gpio:signal_go_proto",
        "//intrinsic/hardware/gripper/eoat:gripper_config_go_proto",
        "//intrinsic/hardware/gripper/eoat:eoat_service_go_proto",
        "//intrinsic/hardware/proto:settings_go_proto",
        "//intrinsic/kinematics/types:dynamic_limits_check_mode_go_proto",
        "//intrinsic/skills/proto:skill_parameter_metadata_go_proto",
        "//intrinsic/skills/proto:error_go_proto",
        "//intrinsic/perception/proto:pose_estimate_in_root_go_proto",
        "//intrinsic/world/proto:object_world_refs_go_proto",
        "//intrinsic/world/proto:collision_action_go_proto",
        "//intrinsic/world/proto:collision_settings_go_proto",
        "//intrinsic/math/proto:vector2_go_proto",
        "//intrinsic/geometry/proto:axis_aligned_bounding_box_go_proto",
        "//intrinsic/geometry/proto:oriented_bounding_box_go_proto",
        "//intrinsic/math/proto:array_go_proto",
        "//intrinsic/math/proto:twist_go_proto",
        "//intrinsic/perception/proto:distortion_params_go_proto",
        "//intrinsic/perception/proto:dimensions_go_proto",
        "//intrinsic/perception/proto:intrinsic_params_go_proto",
        "//intrinsic/perception/proto:camera_params_go_proto",
        "//intrinsic/perception/proto:image_buffer_go_proto",
        "//intrinsic/geometry/service:geometry_storage_refs_go_proto",
        "//intrinsic/geometry/service:transformed_geometry_storage_refs_go_proto",
        "//intrinsic/geometry/proto:octree_go_proto",
        "//intrinsic/geometry/proto:mesh_octree_wrapping_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/geometry/proto:triangle_mesh_go_proto",
        "//intrinsic/geometry/proto:lazy_exact_geometry_go_proto",
        "//intrinsic/world/proto:geometry_component_go_proto",
        "//intrinsic/world/proto:gripper_component_go_proto",
        "//intrinsic/perception/proto:frame_go_proto",
        "//intrinsic/perception/proto:vector_go_proto",
        "//intrinsic/perception/proto:pattern_detection_result_go_proto",
        "//intrinsic/perception/proto:intrinsic_calibration_go_proto",
        "//intrinsic/perception/proto:hand_eye_calibration_go_proto",
        "//intrinsic/perception/proto:camera_drivers_go_proto",
        "//intrinsic/perception/proto:camera_identifier_go_proto",
        "//intrinsic/perception/proto:camera_settings_go_proto",
        "//intrinsic/perception/proto:sensor_config_go_proto",
        "//intrinsic/perception/proto:camera_config_go_proto",
        "//intrinsic/math/proto:affine_go_proto",
        "//intrinsic/perception/proto:pose_estimation_result_go_proto",
        "//intrinsic/scene/proto/v1:entity_go_proto",
        "//intrinsic/scene/proto/v1:object_properties_go_proto",
        "//intrinsic/scene/proto/v1:simulation_spec_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/skills/proto:footprint_go_proto",
        "//intrinsic/geometry/proto:renderable_go_proto",
        "//intrinsic/geometry/proto:geometry_go_proto",
        "//intrinsic/geometry/service:geometry_service_types_go_proto",
        "//intrinsic/world/proto:object_world_updates_go_proto",
        "//intrinsic/skills/proto:prediction_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
        "//intrinsic/skills/proto:equipment_go_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/skills/proto:skill_service_go_grpc_proto",
        "//intrinsic/logging/proto:log_item_go_proto",
    ],
    deps = [":log_dispatcher_service"],
)

go_grpc_library(
    name = "log_dispatcher_service_go_grpc_proto",
    srcs = [":log_dispatcher_service"],
    deps = [
        ":bag_metadata_go_proto",
        ":blob_go_proto",
        ":context_go_proto",
        ":critical_event_log_go_proto",
        ":flowstate_event_go_proto",
        "//intrinsic/executive/proto:log_items_go_proto",
        "//intrinsic/geometry/proto:axis_aligned_bounding_box_go_proto",
        "//intrinsic/geometry/proto:geometry_go_proto",
        "//intrinsic/geometry/proto:lazy_exact_geometry_go_proto",
        "//intrinsic/geometry/proto:mesh_octree_wrapping_go_proto",
        "//intrinsic/geometry/proto:octree_go_proto",
        "//intrinsic/geometry/proto:oriented_bounding_box_go_proto",
        "//intrinsic/geometry/proto:primitives_go_proto",
        "//intrinsic/geometry/proto:renderable_go_proto",
        "//intrinsic/geometry/proto:triangle_mesh_go_proto",
        "//intrinsic/geometry/service:geometry_service_types_go_proto",
        "//intrinsic/geometry/service:geometry_storage_refs_go_proto",
        "//intrinsic/geometry/service:transformed_geometry_storage_refs_go_proto",
        "//intrinsic/hardware/gpio:signal_go_proto",
        "//intrinsic/hardware/gripper/eoat:eoat_service_go_proto",
        "//intrinsic/hardware/gripper/eoat:gripper_config_go_proto",
        "//intrinsic/hardware/gripper/service/proto:generic_gripper_go_proto",
        "//intrinsic/hardware/proto:settings_go_proto",
        "//intrinsic/icon/proto:cart_space_go_proto",
        "//intrinsic/icon/proto:generic_part_config_go_proto",
        "//intrinsic/icon/proto:io_block_go_proto",
        "//intrinsic/icon/proto:joint_space_go_proto",
        "//intrinsic/icon/proto:part_status_go_proto",
        "//intrinsic/icon/proto:safety_status_go_proto",
        "//intrinsic/icon/proto:types_go_proto",
        "//intrinsic/kinematics/proto:kinematics_go_proto",
        "//intrinsic/kinematics/proto:skeleton_go_proto",
        "//intrinsic/kinematics/types:dynamic_limits_check_mode_go_proto",
        "//intrinsic/kinematics/types:joint_limits_go_proto",
        "//intrinsic/logging/errors/proto:error_report_go_proto",
        "//intrinsic/logging/proto:log_item_go_proto",
        "//intrinsic/math/proto:affine_go_proto",
        "//intrinsic/math/proto:array_go_proto",
        "//intrinsic/math/proto:matrix_go_proto",
        "//intrinsic/math/proto:point_go_proto",
        "//intrinsic/math/proto:pose_go_proto",
        "//intrinsic/math/proto:quaternion_go_proto",
        "//intrinsic/math/proto:twist_go_proto",
        "//intrinsic/math/proto:vector2_go_proto",
        "//intrinsic/math/proto:vector3_go_proto",
        "//intrinsic/perception/proto:camera_config_go_proto",
        "//intrinsic/perception/proto:camera_drivers_go_proto",
        "//intrinsic/perception/proto:camera_identifier_go_proto",
        "//intrinsic/perception/proto:camera_params_go_proto",
        "//intrinsic/perception/proto:camera_settings_go_proto",
        "//intrinsic/perception/proto:dimensions_go_proto",
        "//intrinsic/perception/proto:distortion_params_go_proto",
        "//intrinsic/perception/proto:frame_go_proto",
        "//intrinsic/perception/proto:hand_eye_calibration_go_proto",
        "//intrinsic/perception/proto:image_buffer_go_proto",
        "//intrinsic/perception/proto:intrinsic_calibration_go_proto",
        "//intrinsic/perception/proto:intrinsic_params_go_proto",
        "//intrinsic/perception/proto:pattern_detection_result_go_proto",
        "//intrinsic/perception/proto:pose_estimate_in_root_go_proto",
        "//intrinsic/perception/proto:pose_estimation_result_go_proto",
        "//intrinsic/perception/proto:sensor_config_go_proto",
        "//intrinsic/perception/proto:vector_go_proto",
        "//intrinsic/resources/proto:resource_handle_go_proto",
        "//intrinsic/scene/proto/v1:entity_go_proto",
        "//intrinsic/scene/proto/v1:object_properties_go_proto",
        "//intrinsic/scene/proto/v1:scene_object_go_proto",
        "//intrinsic/scene/proto/v1:simulation_spec_go_proto",
        "//intrinsic/skills/proto:equipment_go_proto",
        "//intrinsic/skills/proto:error_go_proto",
        "//intrinsic/skills/proto:footprint_go_proto",
        "//intrinsic/skills/proto:prediction_go_proto",
        "//intrinsic/skills/proto:skill_parameter_metadata_go_proto",
        "//intrinsic/skills/proto:skill_service_go_grpc_proto",
        "//intrinsic/skills/proto:skills_go_proto",
        "//intrinsic/util/status:extended_status_go_proto",
        "//intrinsic/world/proto:collision_action_go_proto",
        "//intrinsic/world/proto:collision_settings_go_proto",
        "//intrinsic/world/proto:geometry_component_go_proto",
        "//intrinsic/world/proto:gripper_component_go_proto",
        "//intrinsic/world/proto:object_world_refs_go_proto",
        "//intrinsic/world/proto:object_world_updates_go_proto",
    ],
)

proto_library(
    name = "bag_metadata_proto",
    srcs = ["bag_metadata.proto"],
    deps = [
        "@com_google_protobuf//:timestamp_proto",
    ],
)

cc_proto_library(
    name = "bag_metadata_cc_proto",
    deps = [":bag_metadata_proto"],
)

py_proto_library(
    name = "bag_metadata_proto_py_pb2",
    deps = [":bag_metadata_proto"],
)

go_proto_library(
    name = "bag_metadata_go_proto",
    deps = [":bag_metadata_proto"],
)
