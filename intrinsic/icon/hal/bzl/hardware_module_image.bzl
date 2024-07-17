# Copyright 2023 Intrinsic Innovation LLC

"""Build rules for creating Hardware Module container images."""

load("//bazel:container.bzl", "container_image")
load("//intrinsic/icon/hal/bzl:hardware_module_binary.bzl", hardware_module_binary_macro = "hardware_module_binary")

def _path_in_container(target):
    """Calculates the absolute path to the executable of a Bazel target.

    Args:
        target: The Bazel target label (e.g., "@foo//x/y:z", "//x/z:z", ":z", "bar:z").

    Returns:
        The absolute path to the executable.
    """

    if target.startswith("@"):
        # External workspace target
        workspace_name = target.split("/")[0][1:]
        path = "/external/%s/%s" % (workspace_name, target.split("//")[1])
        path = path.replace(":", "/")
    elif target.startswith("//"):
        # Absolute target within the main workspace
        path = target[1:].replace(":", "/")
    else:
        # Target within the current package
        package_path = native.package_name() + "/"
        if target.startswith(":"):
            path = package_path + target[1:]
        else:
            path = package_path + target.replace(":", "/")

    return path

def _build_symlink(file, path_prefix):
    """Creates a symlink from <path_prefix>/<file name> to <file>."""
    file_target = Label(file)
    package_path = file_target.package
    file_name = file_target.name
    symlink = path_prefix + file_name
    return {symlink: "/" + package_path + "/" + file_name}

def hardware_module_image(
        name,
        hardware_module_lib = None,
        hardware_module_binary = None,
        extra_files = [],
        base_image = Label("@distroless_base_amd64_oci"),
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

    # Add symlinks from "/data/..." to all `extra_files` to avoid
    # leaking the internal directory structure.
    symlinks = {}
    for file in extra_files:
        symlinks.update(_build_symlink(file, "/data/"))

    # init_hwm is a wrapper to work around the restart backoff of Kubernetes.
    init_hwm_tar = "//intrinsic/icon/utils:init_hwm_tar"
    init_hwm_path = "/init_hwm"

    # Resources use the resource_context for configuration. They should not be called with `--config_pbtxt_file`.
    resource_entrypoint = [
        init_hwm_path,
        "--",
        _path_in_container(hardware_module_binary),
    ]

    init_hwm_layer = init_hwm_tar

    layers = kwargs.get("layers", [])
    layers.append(init_hwm_layer)
    kwargs["layers"] = layers

    container_image(
        name = name,
        base = base_image,
        data_path = "/",
        files = [hardware_module_binary] + extra_files,
        symlinks = symlinks,
        entrypoint = resource_entrypoint,
        labels = {
            "ai.intrinsic.hardware-module-image-name": name,
        },
        **kwargs
    )
