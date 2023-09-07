# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

# Templates used by the external inctl tool.
package(default_visibility = ["//intrinsic/tools/inctl/cmd/bazel:__subpackages__"])

exports_files(
    srcs = [
        "BUILD",
        "WORKSPACE.template",
    ],
    visibility = [
        "//intrinsic/tools/inctl/cmd/bazel:__subpackages__",
    ],
)

genrule(
    name = "bazelrc",
    srcs = ["//:.bazelrc"],
    outs = ["bazelrc.template"],
    cmd = "cat $< " +
          # Remove copyright notice if present.
          r"| perl -0777pe 's/# Copyright(.*?)\n\n//s' " +
          # Remove all lines starting with "build:" plus preceding comment and empty lines.
          r"| perl -0777pe 's/(^\s*\n)*(^#.*\n)*(^build:.*\n)+//mg' " +
          "> $@",
)
