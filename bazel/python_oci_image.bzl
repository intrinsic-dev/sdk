# Copyright 2023 Intrinsic Innovation LLC

"""Helpers for dealing with Python docker images."""

load("@aspect_bazel_lib//lib:tar.bzl", "mtree_mutate", "mtree_spec", "tar")
load(
    "//bazel:container.bzl",
    "container_image",
)

def python_layers(name, binary, **kwargs):
    """Create list of layers for a py_binary target.

    In insrc, we use three layers for the interpreter, third-party dependencies, and application code.

    The setup is adapted from https://github.com/aspect-build/bazel-examples/blob/main/oci_python_image/py_layer.bzl.

    Args:
        name: prefix for generated targets, to ensure they are unique within the package
        binary: the py_binary target.
        **kwargs: extra arguments to pass on to the layers.
    Returns:
        a list of labels for the layers, which are tar files
    """

    binary_label = native.package_relative_label(binary)
    binary_path = "/" + binary_label.package + "/" + binary_label.name
    if kwargs.get("cmd") == None:
        kwargs["cmd"] = [kwargs.get("directory", "") + binary_path]

    layers = []

    # Produce the manifest for a tar file of our py_binary, but don't tar it up yet, so we can split
    # into fine-grained layers for better docker performance.
    mtree_spec(
        name = name + "_tar_manifest_raw",
        srcs = [binary],
    )

    # ADDITION: Handle local_repository sub repos by removing '../' and ' external/' from paths.
    # Without this the resulting image manifest is malformed and tools like dive cannot open the image.
    native.genrule(
        name = name + "_tar_manifest_filtered",
        srcs = [":" + name + "_tar_manifest_raw"],
        outs = [name + "_tar_manifest_filtered.spec"],
        cmd = "sed -e 's/^\\.\\.\\///' $< | sed -e 's/ external\\///g' >$@",
    )

    # Apply mutations for path prefixes
    mtree_mutate(
        name = name + "_tar_manifest_prefix",
        mtree = ":" + name + "_tar_manifest_filtered",
        # BUG: https://github.com/bazel-contrib/bazel-lib/issues/946
        # strip_prefix = kwargs.pop("data_path", None),
        package_dir = kwargs.pop("directory", None),
        # BUG: https://github.com/bazel-contrib/bazel-lib/pull/948
        awk_script = Label("@aspect_bazel_lib//lib/private:modify_mtree.awk"),
    )

    # Workaround unsupported "strip_prefix"
    native.genrule(
        name = name + "_tar_manifest",
        srcs = [":" + name + "_tar_manifest_prefix"],
        outs = [name + "_tar_manifest.spec"],
        cmd = "sed -e 's,^/,,' $< >$@",
    )

    # One layer with only the python interpreter.
    # WORKSPACE: ".runfiles/local_config_python_x86_64-unknown-linux-gnu/"
    # Bzlmod: "runfiles/rules_python~0.27.1~python~python_3_11_x86_64-unknown-linux-gnu/"
    PY_INTERPRETER_REGEX = r"\.runfiles/\S*python\S*_x86_64-unknown-linux-gnu/"

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
        compress = "gzip",
    )
    layers.append(":" + name + "_interpreter_layer")

    # Attempt to match all external (3P) dependencies. Since these can come in as either
    # `requirement` or native Bazel deps, do our best to guess the runfiles path.
    PACKAGES_REGEX = "\\S*\\.runfiles/\\S*\\(site-packages\\|com_\\|pip_deps_\\)"

    # One layer with the third-party pip packages.
    # To make sure some dependencies with surprising paths are not included twice, exclude the interpreter from the site-packages layer.
    native.genrule(
        name = name + "_packages_tar_manifest",
        srcs = [":" + name + "_tar_manifest"],
        outs = [name + "_packages_tar_manifest.spec"],
        cmd = "if ! grep -v '{}' $< | grep '{}' >$@; then touch $@; fi".format(PY_INTERPRETER_REGEX, PACKAGES_REGEX),
    )

    tar(
        name = name + "_packages_layer",
        srcs = [binary],
        mtree = ":" + name + "_packages_tar_manifest",
        compress = "gzip",
    )
    layers.append(":" + name + "_packages_layer")

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
        compress = "gzip",
    )
    layers.append(":" + name + "_app_layer")

    return layers

def python_oci_image(
        name,
        binary,
        base = Label("@distroless_python3"),
        extra_tars = None,
        symlinks = None,
        **kwargs):
    """Wrapper for creating a oci_image from a py_binary target.

    Will create both an oci_image ($name) and a container_tarball ($name.tar) target.

    The setup is inspired by https://github.com/aspect-build/bazel-examples/blob/main/oci_python_image/hello_world/BUILD.bazel.

    Args:
      name: name of the image.
      base: base image to use.
      binary: the py_binary target.
      extra_tars: additional layers to add to the image with e.g. supporting files.
      symlinks: if specified, symlinks to add to the final image (analogous to rules_docker container_image#sylinks).
      **kwargs: extra arguments to pass on to the oci_image target.
    """

    layers = python_layers(name, binary, **kwargs)

    if extra_tars:
        layers.extend(extra_tars)

    container_image(
        name = name,
        base = base,
        layers = layers,
        symlinks = symlinks,
        **kwargs
    )
