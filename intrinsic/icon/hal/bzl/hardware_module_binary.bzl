# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""
Create an executable for a given plugin implementation.

The rule adds necessary driver code around the plugin interface implementation
to guarantee a guided execution of the plugin. This further lets a plugin developer focus on
the essential implementation of the interface rather than duplicating boilerplate code.
"""

def hardware_module_binary(
        name,
        hardware_module_lib,
        sdk_bazel_module = "",
        **kwargs):
    """Creates a binary for a hardware module.

    This can be run directly, as a standard hardware module, or as a resource.

    Args:
      name: The name of the binary.
      hardware_module_lib: The C++ library that defines the hardware module to
          generate an image for.
      sdk_bazel_module: Bazel module name for the SDK when used from a different WORKSPACE
      **kwargs: Additional arguments to pass to cc_binary.
    """
    native.cc_binary(
        name = name,
        srcs = [sdk_bazel_module + "//intrinsic/icon/hal:hardware_module_main"],
        deps = [hardware_module_lib] + [
            "@com_google_absl//absl/container:flat_hash_set",
            "@com_google_absl//absl/flags:flag",
            "@com_google_absl//absl/log",
            "@com_google_absl//absl/log:check",
            "@com_google_absl//absl/status",
            "@com_google_absl//absl/status:statusor",
            "@com_google_absl//absl/strings",
            sdk_bazel_module + "//intrinsic/icon/control:realtime_clock_interface",
            sdk_bazel_module + "//intrinsic/icon/hal:hardware_module_config_cc_proto",
            sdk_bazel_module + "//intrinsic/icon/hal:hardware_module_registry",
            sdk_bazel_module + "//intrinsic/icon/hal:hardware_module_runtime",
            sdk_bazel_module + "//intrinsic/icon/hal:module_config",
            sdk_bazel_module + "//intrinsic/icon/hal:realtime_clock",
            sdk_bazel_module + "//intrinsic/icon/release/portable:init_xfa_absl",
            sdk_bazel_module + "//intrinsic/icon/release:file_helpers",
            sdk_bazel_module + "//intrinsic/util/proto:any",
            sdk_bazel_module + "//intrinsic/util/proto:get_text_proto",
            sdk_bazel_module + "//intrinsic/util/thread",
            sdk_bazel_module + "//intrinsic/util/thread:util",
            sdk_bazel_module + "//intrinsic/util:memory_lock",
            sdk_bazel_module + "//intrinsic/icon/release:status_helpers",
        ],
        **kwargs
    )
