# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Libraries related to Realtime Control Layer Parts.

proto_library(
    name = "realtime_part_config_proto",
    srcs = ["realtime_part_config.proto"],
    visibility = ["//intrinsic:__subpackages__"],
    deps = ["@com_google_protobuf//:any_proto"],
)

cc_proto_library(
    name = "realtime_part_config_cc_proto",
    deps = [":realtime_part_config_proto"],
)

proto_library(
    name = "mode_of_safe_operation_limits_config_proto",
    srcs = ["mode_of_safe_operation_limits_config.proto"],
    visibility = ["//intrinsic:__subpackages__"],
)

cc_proto_library(
    name = "mode_of_safe_operation_limits_config_cc_proto",
    deps = [":mode_of_safe_operation_limits_config_proto"],
)
