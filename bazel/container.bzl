# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with the rules_docker->rules_oci transition.
."""

load(
    "@rules_oci//oci:defs.bzl",
    "oci_image",
    "oci_load",
)
load("@rules_pkg//pkg:tar.bzl", "pkg_tar")

def container_tarball(name, **kwargs):
    load_name = "%s_load" % name
    oci_load(
        name = load_name,
        **kwargs
    )

    native.filegroup(
        name = name,
        srcs = [load_name],
        output_group = "tarball",
    )

def _symlink_tarball_impl(ctx):
    ctx.actions.symlink(output = ctx.outputs.output, target_file = ctx.attr.src[OutputGroupInfo].tarball.to_list()[0])

_symlink_tarball = rule(
    implementation = _symlink_tarball_impl,
    doc = "Creates a symlink to tarball.tar in src's DefaultInfo at output",
    attrs = {
        "src": attr.label(
            providers = [OutputGroupInfo],
            mandatory = True,
        ),
        "output": attr.output(),
    },
)

def container_layer(name, **kwargs):
    pkg_tar(
        name = name,
        extension = "tar.gz",
        compressor_args = "--fast",
        package_dir = kwargs.pop("directory", None),
        strip_prefix = kwargs.pop("data_path", None),
        srcs = kwargs.pop("files", None),
        deps = kwargs.pop("tars", None),
        **kwargs
    )

# buildozer: disable=function-docstring-args
def container_image(
        name,
        base = None,
        data_path = None,
        directory = None,
        entrypoint = None,
        layers = None,
        tars = None,
        files = None,
        symlinks = None,
        labels = None,
        **kwargs):
    """Wrapper for creating an oci_image from a rules_docker container_image target.

    Will create both an oci_image ($name) and a container_tarball ($name.tar) target.

    Note that it does not support the experimental_tarball_format attribute:
    - All tarballs created by this macro will be in .tar.gz format.
    - Existing tarballs won't be compressed if they are not already compressed.

    See https://docs.aspect.build/guides/rules_oci_migration/#container_image for the official conversion documentation.
    """
    if not layers:
        layers = []

    if tars:
        container_layer(
            name = name + "_tar_layer",
            tars = tars,
            data_path = data_path,
            directory = directory,
            compatible_with = kwargs.get("compatible_with"),
            visibility = kwargs.get("visibility"),
            testonly = kwargs.get("testonly"),
        )
        layers.append(name + "_tar_layer")

    if files:
        container_layer(
            name = name + "_files_layer",
            files = files,
            data_path = data_path,
            directory = directory,
            compatible_with = kwargs.get("compatible_with"),
            visibility = kwargs.get("visibility"),
            testonly = kwargs.get("testonly"),
        )
        layers.append(name + "_files_layer")

    if symlinks:
        container_layer(
            name = name + "_symlink_layer",
            symlinks = symlinks,
            data_path = "/",
            compatible_with = kwargs.get("compatible_with"),
            visibility = kwargs.get("visibility"),
            testonly = kwargs.get("testonly"),
        )
        layers.append(name + "_symlink_layer")

    oci_image(
        name = name,
        base = base,
        tars = layers,
        entrypoint = entrypoint,
        labels = labels,
        **kwargs
    )

    tag = "%s:latest" % name
    package = native.package_name()
    if package:
        tag = "%s/%s" % (package, tag)
    container_tarball(
        name = "_%s_tarball" % name,
        image = name,
        compatible_with = kwargs.get("compatible_with"),
        repo_tags = [tag],
        visibility = kwargs.get("visibility"),
        testonly = kwargs.get("testonly"),
    )

    _symlink_tarball(
        name = "_%s_tarball_symlink" % name,
        src = "_%s_tarball_load" % name,
        output = "%s.tar" % name,
        compatible_with = kwargs.get("compatible_with"),
        visibility = kwargs.get("visibility"),
        testonly = kwargs.get("testonly"),
    )
