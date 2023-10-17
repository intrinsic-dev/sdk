# Copyright 2023 Intrinsic Innovation LLC

"""
This module contains rules to represent hierarchies of flatbuffer messages.

The fbs_library rule is used to collect schemas into logical libraries, and
represent the dependencies between them. Note that no language-specific code is
generated. (See //intrinsic/platform:cc.bzl and
//intrinsic/platform:py.bzl for language-specific code generation.)

Usage:

load("//intrinsic/platform:fbs_library.bzl", "fbs_library")

# Collects Flatbuffer schemas for bar.fbs, and sets the optional build parameter
# 'gen_mutable' to False.
fbs_library(
  name = "bar_fbs",
  srcs = ["bar.fbs"],
  gen_mutable = False,  # Optionally generates mutable libraries (default True)
)

# Collects Flatbuffer schemas in foo.fbs, which includes bar.fbs.
fbs_library(
  name = "foo_fbs",
  srcs = ["foo.fbs"],
  deps = [":bar_fbs"]
)
"""

FbsInfo = provider(
    fields = [
        "direct_fbs_srcs",
        "indirect_fbs_srcs",
        "direct_include_dirs",
        "transitive_include_dirs",
        "gen_mutable",
    ],
)

def _fbs_library_impl(ctx):
    transitive_include_dirs = []
    indirect_fbs_srcs = []
    for dep in ctx.attr.deps:
        indirect_fbs_srcs.append(dep[FbsInfo].direct_fbs_srcs)
        indirect_fbs_srcs.append(dep[FbsInfo].indirect_fbs_srcs)

        transitive_include_dirs.append(dep[FbsInfo].direct_include_dirs)
        transitive_include_dirs.append(dep[FbsInfo].transitive_include_dirs)

    fbs_src_files = depset(transitive = [a.files for a in ctx.attr.srcs])

    direct_include_dirs = [ctx.label.workspace_root]
    for in_f in fbs_src_files.to_list():
        direct_include_dirs.append(in_f.dirname)

    fbs_info_out = FbsInfo(
        direct_fbs_srcs = fbs_src_files,
        indirect_fbs_srcs = depset(transitive = indirect_fbs_srcs),
        direct_include_dirs = depset(direct_include_dirs),
        transitive_include_dirs = depset(transitive = transitive_include_dirs),
        gen_mutable = ctx.attr.gen_mutable,
    )
    return [fbs_info_out]

fbs_library = rule(
    implementation = _fbs_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "gen_mutable": attr.bool(default = True),
        "deps": attr.label_list(),
    },
    provides = [FbsInfo],
)

def make_flatc_include_args(fbs_info, ctx):
    args = ctx.actions.args()
    args.add("-I", ".")  # need working dir

    dirs = depset(transitive = [fbs_info.direct_include_dirs, fbs_info.transitive_include_dirs])
    args.add_all(dirs, before_each = "-I")

    return args
