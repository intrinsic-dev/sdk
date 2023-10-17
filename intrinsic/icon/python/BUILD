# Copyright 2023 Intrinsic Innovation LLC

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

package(default_visibility = ["//visibility:public"])

py_binary(
    name = "get_metadata",
    srcs = ["examples/get_metadata.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/util/grpc:connection",
        "@com_google_absl_py//absl:app",
        "@com_google_absl_py//absl/flags",
    ],
)

py_library(
    name = "icon",
    srcs = [
        "_session.py",
        "actions.py",
        "errors.py",
        "icon_api.py",
        "reactions.py",
        "state_variable_path.py",
    ],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/icon/proto:matrix_conversions",  # buildcleaner: keep to allow import
        "//intrinsic/icon/proto:service_py_pb2",
        "//intrinsic/icon/proto:service_py_pb2_grpc",
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/icon/proto:types_py_pb2",
        "//intrinsic/logging/proto:context_py_pb2",
        "//intrinsic/util/grpc:connection",
        "//intrinsic/util/grpc:interceptor",
        requirement("grpcio"),
        "@com_google_absl_py//absl/logging",
        "@com_google_googleapis//google/rpc:code_py_proto",
        "@com_google_googleapis//google/rpc:status_py_proto",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "icon_logging",
    srcs = ["icon_logging.py"],
    deps = [
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/logging/proto:log_item_py_pb2",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "create_action_utils",
    srcs = ["create_action_utils.py"],
    deps = [
        "//intrinsic/icon/actions:point_to_point_move_utils",
        "//intrinsic/icon/actions:stop_utils",
        "//intrinsic/icon/actions:tare_force_torque_sensor_utils",
        "//intrinsic/icon/actions:trajectory_tracking_action_utils",
        "//intrinsic/icon/actions:wait_for_settling_utils",
    ],
)

py_test(
    name = "create_action_utils_test",
    srcs = ["create_action_utils_test.py"],
    deps = [
        ":create_action_utils",
        "//intrinsic/icon/actions:point_to_point_move_utils",
        "//intrinsic/icon/actions:stop_utils",
        "//intrinsic/icon/actions:tare_force_torque_sensor_utils",
        "//intrinsic/icon/actions:trajectory_tracking_action_utils",
        "//intrinsic/icon/actions:wait_for_settling_utils",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
        requirement("numpy"),
    ],
)

py_test(
    name = "icon_logging_test",
    srcs = ["icon_logging_test.py"],
    deps = [
        ":icon_logging",
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/logging/proto:log_item_py_pb2",
        "//intrinsic/math/proto:pose_py_pb2",
        "//intrinsic/math/proto:vector3_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "icon_test",
    srcs = ["icon_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/icon/proto:safety_status_py_pb2",
        "//intrinsic/icon/proto:service_py_pb2",
        "//intrinsic/icon/proto:types_py_pb2",
        "//intrinsic/logging/proto:context_py_pb2",
        "//intrinsic/util/grpc:connection",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_binary(
    name = "joint_move",
    srcs = ["examples/joint_move.py"],
    python_version = "PY3",
    deps = [
        ":create_action_utils",
        ":icon",
        "//intrinsic/util/grpc:connection",
        requirement("grpcio"),
        "@com_google_absl_py//absl:app",
        "@com_google_absl_py//absl/flags",
        requirement("numpy"),
    ],
)

py_binary(
    name = "operational_state",
    srcs = ["examples/operational_state.py"],
    python_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/util/grpc:connection",
        "@com_google_absl_py//absl:app",
        "@com_google_absl_py//absl/flags",
    ],
)

py_test(
    name = "_session_test",
    srcs = ["_session_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/icon/proto:service_py_pb2",
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/icon/proto:types_py_pb2",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_test(
    name = "actions_test",
    srcs = ["actions_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/icon/actions:point_to_point_move_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_test(
    name = "reactions_test",
    srcs = ["reactions_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":icon",
        "//intrinsic/icon/proto:types_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_test(
    name = "proto_test",
    srcs = ["proto_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//intrinsic/icon/proto:cart_space_py_pb2",
        "//intrinsic/icon/proto:ik_options_py_pb2",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/icon/proto:matrix_py_pb2",
        "//intrinsic/icon/proto:part_status_py_pb2",
        "//intrinsic/icon/proto:service_py_pb2",
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/icon/proto:types_py_pb2",
        "@com_google_absl_py//absl/testing:absltest",
        "@com_google_googleapis//google/rpc:status_py_proto",
    ],
)

py_test(
    name = "grpc_proto_test",
    srcs = ["grpc_proto_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//intrinsic/icon/proto:cart_space_py_pb2",
        "//intrinsic/icon/proto:ik_options_py_pb2",
        "//intrinsic/icon/proto:joint_space_py_pb2",
        "//intrinsic/icon/proto:matrix_py_pb2",
        "//intrinsic/icon/proto:part_status_py_pb2",
        "//intrinsic/icon/proto:service_py_pb2",
        "//intrinsic/icon/proto:service_py_pb2_grpc",
        "//intrinsic/icon/proto:streaming_output_py_pb2",
        "//intrinsic/icon/proto:types_py_pb2",
        requirement("grpcio"),
        "@com_google_absl_py//absl/testing:absltest",
    ],
)

py_package(
    name = "icon_py_packages",
    packages = [
        "intrinsic",
    ],
    deps = [
        ":create_action_utils",
        ":icon",
    ],
)

py_wheel(
    name = "icon_wheel",
    distribution = "icon",
    requires = [
        "grpcio",
        "google-api-core",
        "google-api-python-client",
        "absl-py",
        "numpy",
        "googleapis-common-protos",
    ],
    version = "0.0.1",
    deps = [":icon_py_packages"],
)
