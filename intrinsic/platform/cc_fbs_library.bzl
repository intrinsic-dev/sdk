# Copyright 2023 Intrinsic Innovation LLC

"""
This module contains aspect and rule definitions to generate C++ flatbuffers sources.

The cc_fbs_library rule ensures that flatc is invoked to generate C++ sources
for the messages in a fbs_library and its dependencies.

Usage:

load("//intrinsic/platform:fbs_library.bzl", "fbs_library")
load("//intrinsic/platform:cc_fbs_library.bzl", "cc_fbs_library")

# Collects Flatbuffer schemas for bar.fbs.
fbs_library(
  name = "bar_fbs",
  srcs = ["bar.fbs"]
)

# Collects Flatbuffer schemas in foo.fbs, which includes bar.fbs.
fbs_library(
  name = "foo_fbs",
  srcs = ["foo.fbs"],
  deps = [":bar_fbs"]
)

# Generates C++ code for foo_fbs and its dependencies. Transitive dependencies
# will automatically be generated if required (so bar_fbs_cc doesn't need to be
# explicitly defined if it's not directly used by C++ code).
cc_fbs_library(
  name = "foo_fbs_cc",
  deps = [":foo_fbs"]
)

cc_binary(
  name = "my_binary",
  deps = [":foo_fbs_cc"],
)
"""

load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")
load("//intrinsic/platform:fbs_library.bzl", "FbsInfo", "make_flatc_include_args")
load("@bazel_skylib//lib:paths.bzl", "paths")
def use_cpp_toolchain():
    return ["@bazel_tools//tools/cpp:toolchain_type"]

# The FbsCcInfo provider wraps a CcInfo with the C++ generated sources for a
# rule's FbsInfo. (This approach, while seeming odd on the surface, is in line
# with the CcInfo provider's documentation. "If it is not intended for the rule
# to be depended on by C++, the rule should wrap the CcInfo in some other
# provider.")
FbsCcInfo = provider(
    fields = ["ccinfo"],
)

def _gen_flatbuffers_cc_aspect_impl(target, ctx):
    """
    Aspect that generates C++ sources for a given rule with FbsInfo provider.
    """

    # Declare the files that will be created by flatc, derived from the input filenames.
    generated_files = []
    for in_f in target[FbsInfo].direct_fbs_srcs.to_list():
        name_without_extension = paths.split_extension(in_f.basename)[0]
        generated_files.append(ctx.actions.declare_file(name_without_extension + "_generated.h", sibling = in_f))

    # generated_files will be empty when this aspect visits a rule that doesn't
    # have any direct_fbs_srcs. This case most commonly arises when visiting a
    # rule that applies an aspect to another set of rules to generate the
    # FbsInfo. The rule applying the aspect won't have any direct_fbs_srcs,
    # only transitive srcs.
    if len(generated_files) > 0:
        # Collect fbs files to pass to flatc.
        flatc_input_files = depset(
            transitive = [target[FbsInfo].direct_fbs_srcs, target[FbsInfo].indirect_fbs_srcs],
        )

        args = make_flatc_include_args(target[FbsInfo], ctx)
        args.add("-c")
        args.add_all([
            "--keep-prefix",
            "--reflect-names",
            "--scoped-enums",
        ])
        if target[FbsInfo].gen_mutable:
            args.add("--gen-mutable")
        args.add("-o", generated_files[0].dirname)

        args.add_all(target[FbsInfo].direct_fbs_srcs)

        # Invoke flatc to generate code.
        ctx.actions.run(
            outputs = generated_files,
            inputs = flatc_input_files,
            executable = ctx.file._flatc,
            arguments = [args],
        )

    # Configure the C++ toolchain.
    cc_toolchain = find_cpp_toolchain(ctx)
    feature_configuration = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = cc_toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )

    # Collect CcInfo providers from all dependencies.
    dep_ccinfos = [
        dep[FbsCcInfo].ccinfo
        for dep in ctx.rule.attr.deps
        if FbsCcInfo in dep
    ] + [
        dep[CcInfo]
        for dep in ctx.rule.attr.deps
        if CcInfo in dep
    ]
    compilation_contexts = [
        dep.compilation_context
        for dep in dep_ccinfos
    ] + [ctx.attr._flatbuffers_lib[CcInfo].compilation_context]

    # Compile the generated code.
    (compilation_context, compilation_outputs) = cc_common.compile(
        # Add a suffix to the compile name to avoid collisions when a rule
        # already does its own C++ compilation.
        name = ctx.label.name + "_fbs",
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        srcs = [],
        public_hdrs = generated_files,
        compilation_contexts = compilation_contexts,
    )

    (linking_context, _linking_outputs) = cc_common.create_linking_context_from_compilation_outputs(
        name = ctx.label.name + "_fbs",
        actions = ctx.actions,
        feature_configuration = feature_configuration,
        cc_toolchain = cc_toolchain,
        compilation_outputs = compilation_outputs,
    )

    # Return our compilation context in a CcInfo provider so cc_.* rules can
    # consume the output.
    direct_cc_info = CcInfo(
        compilation_context = compilation_context,
        linking_context = linking_context,
    )

    # Merge the CcInfos and return a FbsCcInfo.
    return FbsCcInfo(ccinfo = cc_common.merge_cc_infos(
        direct_cc_infos = [direct_cc_info] + dep_ccinfos,
        cc_infos = [ctx.attr._flatbuffers_lib[CcInfo]],
    ))

_gen_flatbuffers_cc = aspect(
    implementation = _gen_flatbuffers_cc_aspect_impl,
    required_aspect_providers = [FbsInfo],
    provides = [FbsCcInfo],
    attr_aspects = ["deps"],
    fragments = ["google_cpp", "cpp"],
    attrs = {
        "_flatc": attr.label(
            default = Label("@com_github_google_flatbuffers//:flatc"),
            cfg = "exec",
            allow_single_file = True,
            executable = True,
        ),
        "_flatbuffers_lib": attr.label(default = Label("@com_github_google_flatbuffers//:runtime_cc")),
        "_cc_toolchain": attr.label(default = "@bazel_tools//tools/cpp:current_cc_toolchain"),
    },
    toolchains = use_cpp_toolchain(),
)

def _cc_fbs_library_impl(ctx):
    if len(ctx.attr.deps) != 1:
        fail("only one deps dependency allowed", attr = "deps")
    return ctx.attr.deps[0][FbsCcInfo].ccinfo

cc_fbs_library = rule(
    implementation = _cc_fbs_library_impl,
    provides = [CcInfo],
    attrs = {
        "deps": attr.label_list(aspects = [_gen_flatbuffers_cc]),
    },
    toolchains = use_cpp_toolchain(),
)
