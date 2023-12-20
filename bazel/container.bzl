# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with the rules_docker->rules_oci transition.

."""

load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_pkg//:pkg.bzl", "pkg_tar")

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

    oci_image(
        name = name,
        base = base,
        tars = tars,
        entrypoint = entrypoint,
        labels = labels,
        **kwargs
    )

    oci_tarball(
        name = name + ".tar",
        image = name,
        repo_tags = ["%s/%s:latest" % (native.package_name(), name)],
        **kwargs
    )
