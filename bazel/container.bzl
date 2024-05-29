# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with the rules_docker->rules_oci transition.

."""

load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_pkg//:pkg.bzl", "pkg_tar")

def _symlink_tarball_impl(ctx):
    ctx.actions.symlink(output = ctx.outputs.output, target_file = ctx.file.src)

_symlink_tarball = rule(
    implementation = _symlink_tarball_impl,
    doc = "Creates a symlink to tarball.tar in src's DefaultInfo at output",
    attrs = {
        "src": attr.label(
            allow_single_file = [".tar"],
            mandatory = True,
        ),
        "output": attr.output(),
    },
)

def container_layer(name, files, data_path = None, directory = None, **kwargs):
    pkg_tar(
        name = name,
        compressor_args = "--fast",
        package_dir = directory,
        strip_prefix = data_path,
        srcs = files,
        **kwargs
    )

# buildozer: disable=function-docstring-args
def container_image(
        name,
        base,
        data_path = None,
        directory = None,
        entrypoint = None,
        files = None,
        labels = None,
        layers = None,
        symlinks = None,
        **kwargs):
    """Wrapper for creating an oci_image from a rules_docker container_image target.

    Will create both an oci_image ($name) and an oci_tarball ($name.tar) target.

    See https://docs.aspect.build/guides/rules_oci_migration/#container_image for the official conversion documentation.
    """
    tars = layers or []
    if files:
        pkg_tar(
            name = name + "_main_files",
            compressor_args = "--fast",
            package_dir = directory,
            strip_prefix = data_path,
            srcs = files,
        )
        tars.append(name + "_main_files")

    if symlinks:
        pkg_tar(
            name = name + "_symlink_layer",
            strip_prefix = "/",
            symlinks = symlinks,
        )
        tars.append(name + "_symlink_layer")

    oci_image(
        name = name,
        base = base,
        tars = tars,
        entrypoint = entrypoint,
        labels = labels,
        **kwargs
    )

    tag = "%s:latest" % name
    package = native.package_name()
    if package:
        tag = "%s/%s" % (package, tag)
    oci_tarball(
        name = "_%s_tarball" % name,
        image = name,
        repo_tags = [tag],
        visibility = kwargs.get("visibility"),
        testonly = kwargs.get("testonly"),
    )

    _symlink_tarball(
        name = "_%s_tarball_symlink" % name,
        src = "_%s_tarball" % name,
        output = "%s.tar" % name,
        visibility = kwargs.get("visibility"),
        testonly = kwargs.get("testonly"),
    )
