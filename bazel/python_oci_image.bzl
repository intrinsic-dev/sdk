# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with Python docker images."""

load("@aspect_bazel_lib//lib:tar.bzl", "mtree_spec", "tar")
load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("//bazel:container.bzl", "container_image")

def python_oci_image(
        name,
        binary,
        extra_tars = None,
        symlinks = None,
        **kwargs):
    """Wrapper for creating a oci_image from a py_binary target.

    Will create both an oci_image ($name) and an oci_tarball ($name.tar) target.

    The setup is inspired by https://github.com/aspect-build/bazel-examples/blob/main/oci_python_image/hello_world/BUILD.bazel.

    Args:
      name: name of the image.
      binary: the py_binary target.
      extra_tars: additional layers to add to the image with e.g. supporting files.
      symlinks: if specified, symlinks to add to the final image (analogous to rules_docker container_image#sylinks).
      **kwargs: extra arguments to pass on to the oci_image target.
    """

    # Produce the manifest for a tar file of our py_binary, but don't tar it up yet, so we can split
    # into fine-grained layers for better docker performance.
    mtree_spec(
        name = name + "_tar_manifest_raw",
        srcs = [binary],
    )

    # ADDITION: Handle local_repository sub repos by removing '../' and ' external/' from paths.
    # Without this the resulting image manifest is malformed and tools like dive cannot open the image.
    native.genrule(
        name = name + "_tar_manifest",
        srcs = [":" + name + "_tar_manifest_raw"],
        outs = [name + "_tar_manifest.spec"],
        cmd = "sed -e 's/^..\\///' $< | sed -e 's/ external\\///g' >$@",
    )

    # One layer with only the python interpreter.
    # WORKSPACE: ".runfiles/local_config_python_x86_64-unknown-linux-gnu/"
    # Bzlmod: "runfiles/rules_python~0.27.1~python~python_3_11_x86_64-unknown-linux-gnu/"
    PY_INTERPRETER_REGEX = "\\.runfiles/\\S*_python\\S*_x86_64-unknown-linux-gnu/"

    native.genrule(
        name = name + "_interpreter_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_interpreter_tar_manifest.spec"],
        cmd = "grep '{}' $< >$@".format(PY_INTERPRETER_REGEX),
    )

    tar(
        name = name + "_interpreter_layer",
        srcs = [binary],
        mtree = ":" + name + "_interpreter_tar_manifest",
    )

    # Attempt to match all external (3P) dependencies. Since these can come in as either
    # `requirement` or native Bazel deps, do our best to guess the runfiles path.
    PACKAGES_REGEX = "\\S*\\.runfiles/\\S*\\(site-packages\\|com_\\|pip_deps_\\)"

    # One layer with the third-party pip packages.
    # To make sure some dependencies with surprising paths are not included twice, exclude the interpreter from the site-packages layer.
    native.genrule(
        name = name + "_packages_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_packages_tar_manifest.spec"],
        cmd = "grep -v '{}' $< | grep '{}' >$@".format(PY_INTERPRETER_REGEX, PACKAGES_REGEX),
    )

    tar(
        name = name + "_packages_layer",
        srcs = [binary],
        mtree = ":" + name + "_packages_tar_manifest",
    )

    # Any lines that didn't match one of the two grep above...
    native.genrule(
        name = name + "_app_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_app_tar_manifest.spec"],
        cmd = "grep -v '{}' $< | grep -v '{}' >$@".format(PACKAGES_REGEX, PY_INTERPRETER_REGEX),
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

    container_image(
        name = name,
        layers = [
            ":" + name + "_interpreter_layer",
            ":" + name + "_packages_layer",
            ":" + name + "_app_layer",
            ":" + name + "_symlink_layer",
        ] + (extra_tars if extra_tars else []),
        **kwargs
    )
