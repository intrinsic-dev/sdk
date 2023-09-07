# Copyright 2023 Intrinsic Innovation LLC
# Intrinsic Proprietary and Confidential
# Provided subject to written agreement between the parties.

"""Build rules for creating Hardware Module container images."""

load("@io_bazel_rules_docker//container:container.bzl", "container_image")
load("//intrinsic/icon/hal/bzl:hardware_module_binary.bzl", hardware_module_binary_macro = "hardware_module_binary")

container_dir = "google3"

def _path_in_container(path):
    # BUG in container_image(): https://github.com/bazelbuild/rules_docker/issues/106#issuecomment-1634382529
    # as it is using f.short_path which starts with ../ for external targets: https://github.com/bazelbuild/bazel/issues/8598
    repo = native.repository_name()
    if repo == "@":
        repo += container_dir
    repo = repo[1:]  # strip "@"
    return repo + "/" + native.package_name() + "/" + path

def hardware_module_image(
        name,
        hardware_module_lib = None,
        hardware_module_binary = None,
        extra_files = [],
        base_image = "@distroless_base_amd64//image",
        **kwargs):
    """Generates a Hardware Module image.

    Args:
      name: The name of the hardware module image to build, must end in "_image".
      hardware_module_lib: The C++ library that defines the hardware module to generate an image for. If this arg is set, then `hardware_module_binary` must be unset.
      hardware_module_binary: A binary that implements the hardware module to generate an image for. If this arg is set, then `hardware_module_lib` must be unset.
      extra_files: Extra files to include in the image.
      base_image: The base image to use for the docker_build 'base'.
      **kwargs: Additional arguments to pass to container_image().
    """

    if not name.endswith("_image"):
        fail("hardware_module_image name must end in _image")

    if hardware_module_lib:
        if hardware_module_binary:
            fail("hardware_module_lib and hardware_module_binary were both specified.")

        hardware_module_binary = "_" + name + "_binary"
        hardware_module_binary_macro(
            name = hardware_module_binary,
            hardware_module_lib = hardware_module_lib,
        )

    if not hardware_module_binary:
        fail("specify one of hardware_module_lib or hardware_module_binary")

    container_image(
        name = name,
        base = base_image,
        compression_options = ["--fast"],
        data_path = "/",
        directory = container_dir,
        experimental_tarball_format = "compressed",
        files = [hardware_module_binary] + extra_files,
        entrypoint = [_path_in_container(hardware_module_binary)],
        labels = {
            "ai.intrinsic.hardware-module-image-name": name,
        },
        **kwargs
    )
