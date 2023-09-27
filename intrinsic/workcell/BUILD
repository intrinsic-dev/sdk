# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Workcell Python client library

load("@ai_intrinsic_sdks_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = [
    "//visibility:public",
])

py_library(
    name = "workcell_api",
    srcs = ["workcell_api.py"],
    srcs_version = "PY3",
    deps = [
        "//intrinsic/kubernetes/workcell_spec/proto:installer_py_pb2_grpc",
        "//intrinsic/math/python:data_types",
        "//intrinsic/perception/proto:hand_eye_calibration_py_pb2",
        "//intrinsic/skills/apps/calibration:collect_calibration_data_py_pb2",
        "//intrinsic/skills/apps/calibration:sample_calibration_poses_py_pb2",
        "//intrinsic/skills/proto:skills_py_pb2",
        "//intrinsic/solutions:behavior_tree",
        "//intrinsic/solutions:deployments",
        "//intrinsic/solutions:equipment",
        "//intrinsic/solutions:errors",
        "//intrinsic/solutions:execution",
        "//intrinsic/solutions:perception",
        "//intrinsic/solutions:pose_estimation",
        "//intrinsic/solutions:providers",
        "//intrinsic/solutions:structured_logging",
        "//intrinsic/solutions:utils",
        "//intrinsic/solutions:worlds",
        "//intrinsic/solutions/internal:behavior_call",
        "//intrinsic/world/python:object_world_resources",
        requirement("grpcio"),
    ],
)

py_test(
    name = "workcell_api_test",
    srcs = ["workcell_api_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":workcell_api",
        "@com_google_absl_py//absl/testing:absltest",
    ],
)
