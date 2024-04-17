# Copyright 2023 Intrinsic Innovation LLC

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

genrule(
    name = "bazelversion",
    srcs = ["//:.bazelversion"],
    outs = ["bazelversion.template"],
    cmd = "cat $< > $@",
)

genrule(
    name = "permissive_content_mirror",
    srcs = ["//bazel:content_mirror/permissive.cfg"],
    outs = ["permissive_content_mirror.template"],
    cmd = "cat $< > $@",
)
