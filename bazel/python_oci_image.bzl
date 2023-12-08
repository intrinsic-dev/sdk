# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with Python docker images."""

load("@aspect_bazel_lib//lib:tar.bzl", "mtree_spec", "tar")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_pkg//:pkg.bzl", "pkg_tar")

def python_oci_image(
        name,
        binary,
        symlinks = None,
        **kwargs):
    """Wrapper for creating a oci_image from a py_binary target.

    Will create both an oci_image ($name) and an oci_tarball ($name.tar) target.

    The setup is taken from https://github.com/aspect-build/bazel-examples/blob/main/oci_python_image/hello_world/BUILD.bazel.

    Args:
      name: name of the image.
      binary: the py_binary target.
      symlinks: if specified, symlinks to add to the final image (analogous to rules_docker container_image#sylinks).
      **kwargs: extra arguments to pass on to the oci_image target.
    """

    # Produce the manifest for a tar file of our py_binary, but don't tar it up yet, so we can split
    # into fine-grained layers for better docker performance.
    mtree_spec(
        name = name + "_tar_manifest",
        srcs = [binary],
    )

    # Match *only* external repositories that have the string "python"
    # e.g. this will match
    #   `/$name/$name.runfiles/rules_python~0.21.0~python~python3_9_aarch64-unknown-linux-gnu/bin/python3`
    # but not match
    #   `/$name/$name.runfiles/_main/python_app`.
    PY_INTERPRETER_REGEX = "\\.runfiles/.*python.*-.*/"

    native.genrule(
        name = name + "_interpreter_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_interpreter_tar_manifest.spec"],
        cmd = "grep '{}' $< >$@".format(PY_INTERPRETER_REGEX),
    )

    # One layer with only the python interpreter.
    tar(
        name = name + "_interpreter_layer",
        srcs = [binary],
        mtree = ":" + name + "_interpreter_tar_manifest",
    )

    # Match *only* external pip like repositories that contain the string "site-packages".
    SITE_PACKAGES_REGEX = "\\.runfiles/.*/site-packages/.*"

    native.genrule(
        name = "packages_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = ["packages_tar_manifest.spec"],
        cmd = "grep '{}' $< >$@".format(SITE_PACKAGES_REGEX),
    )

    # One layer with the third-party pip packages.
    tar(
        name = name + "_packages_layer",
        srcs = [binary],
        mtree = ":packages_tar_manifest",
    )

    # Any lines that didn't match one of the two grep above...
    native.genrule(
        name = name + "_app_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_app_tar_manifest.spec"],
        cmd = "grep -v '{}' $< | grep -v '{}' >$@".format(SITE_PACKAGES_REGEX, PY_INTERPRETER_REGEX),
    )

    # ... go into the third layer which is the application. We assume it changes the most frequently.
    tar(
        name = name + "_app_layer",
        srcs = [binary],
        mtree = ":" + name + "_app_tar_manifest",
    )

    # Layer with a single symlink to make the migration to rules_oci from rules_docker/py3_image backwards compatible.
    # This is needed because the Aspect tar rule used above does not support `symlinks` or `package_dir` and I cannot
    # atomically change the entry point in the yaml (in google3).
    pkg_tar(
        name = name + "_symlink_layer",
        strip_prefix = "/",
        symlinks = symlinks,
    )

    oci_image(
        name = name,
        tars = [
            ":" + name + "_interpreter_layer",
            ":" + name + "_packages_layer",
            ":" + name + "_app_layer",
            ":" + name + "_symlink_layer",
        ],
        visibility = ["//visibility:public"],
        **kwargs
    )

    oci_tarball(
        name = name + ".tar",
        image = ":" + name,
        repo_tags = [""],  # We set target tags at runtime.
        visibility = ["//visibility:public"],
    )
