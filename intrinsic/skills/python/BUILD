# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

load("@rules_python//python:defs.bzl", "py_library")
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "skill_interface",
    srcs = ["skill_interface.py"],
    srcs_version = "PY3",
    deps = [
        ":skill_canceller",
        "//intrinsic/geometry/service:geometry_service_py_pb2_grpc",
        "//intrinsic/logging/proto:context_py_pb2",
        "//intrinsic/motion_planning:motion_planner_client_py",
        "//intrinsic/skills/proto:equipment_py_pb2",
        "//intrinsic/skills/proto:footprint_py_pb2",
        "//intrinsic/skills/proto:skill_service_py_pb2",
        "//intrinsic/world/python:object_world_client",
        "//intrinsic/world/python:object_world_ids",
        "//intrinsic/world/python:object_world_resources",
        "@com_google_protobuf//:protobuf_python",
    ],
)

py_library(
    name = "skill_canceller",
    srcs = ["skill_canceller.py"],
)

py_library(
    name = "proto_utils",
    srcs = ["proto_utils.py"],
    srcs_version = "PY3",
    deps = ["@com_google_protobuf//:protobuf_python"],
)

py_package(
    name = "skills_py_packages",
    packages = [
        "intrinsic",
    ],
    deps = [
        ":proto_utils",
        ":skill_interface",
        "//intrinsic/icon/proto:icon_protos",
        "//intrinsic/icon/python:icon",
        "//intrinsic/math/proto:math_protos",
        "//intrinsic/skills/proto:skills_all_protos",
        "//intrinsic/util:decorators",
        "//intrinsic/world/proto:world_protos",
    ],
)

py_wheel(
    name = "skills_wheel",
    distribution = "skills",
    requires = [
        "grpcio",
        "google-api-core",
        "numpy",
        "retrying",
    ],
    version = "0.0.1",
    deps = [":skills_py_packages"],
)
