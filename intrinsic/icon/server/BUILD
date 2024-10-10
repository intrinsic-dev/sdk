# Copyright 2023 Intrinsic Innovation LLC

package(default_visibility = [
    "//visibility:public",
])

cc_library(
    name = "session_instance",
    srcs = ["session_instance.cc"],
    hdrs = ["session_instance.h"],
    deps = [
        ":session_interface",
        "//intrinsic/icon/common:id_types",
        "@com_github_grpc_grpc//:grpc++",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/synchronization",
    ],
)

cc_library(
    name = "session_interface",
    hdrs = ["session_interface.h"],
    deps = [
        "//intrinsic/icon/common:id_types",
        "//intrinsic/icon/common:part_group",
        "//intrinsic/icon/common:slot_part_map",
        "//intrinsic/icon/proto:joint_space_cc_proto",
        "//intrinsic/icon/proto:streaming_output_cc_proto",
        "//intrinsic/icon/proto:types_cc_proto",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/time",
        "@com_google_absl//absl/types:optional",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_library(
    name = "parts_manager",
    srcs = ["parts_manager.cc"],
    hdrs = ["parts_manager.h"],
    deps = [
        "@com_google_absl//absl/base:core_headers",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/synchronization",
    ],
)

cc_test(
    name = "parts_manager_test",
    srcs = ["parts_manager_test.cc"],
    deps = [
        ":parts_manager",
        "//intrinsic/util/testing:gtest_wrapper",
        "@com_google_absl//absl/container:flat_hash_set",
        "@com_google_absl//absl/status",
    ],
)

cc_library(
    name = "operational_state_interface",
    hdrs = ["operational_state_interface.h"],
    deps = [
        "//intrinsic/icon/cc_client:operational_status",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/status:statusor",
    ],
)
