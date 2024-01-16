# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for @io_bazel_rules_docker
"""

load("@io_bazel_rules_docker//container:pull.bzl", "container_pull")
load("@io_bazel_rules_docker//toolchains/docker:toolchain.bzl", "toolchain_configure")

def extension_for_io_bazel_rules_docker():
    container_pull(
        name = "distroless_base_amd64",
        digest = "sha256:eaddb8ca70848a43fab351226d9549a571f68d9427c53356114fedd3711b5d73",
        registry = "gcr.io",
        repository = "distroless/base",
    )

def _extension_for_io_bazel_rules_docker_impl(ctx):  # @unused
    toolchain_configure(
        name = "docker_config",
    )

    extension_for_io_bazel_rules_docker()

    # Source https://github.com/bazelbuild/rules_docker/blob/master/python3/image.bzl
    container_pull(
        name = "py3_image_base",
        registry = "gcr.io",
        repository = "distroless/python3",
        digest = "sha256:2bcee59e0ecbadf01e1b5df29ad27598c7775b822b7f2bfae4a271e2ee139ed4",
    )

extension_for_io_bazel_rules_docker_ext = module_extension(implementation = _extension_for_io_bazel_rules_docker_impl)
