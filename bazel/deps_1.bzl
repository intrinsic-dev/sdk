# Copyright 2023 Intrinsic Innovation LLC

"""Workspace dependencies needed for the Intrinsic SDKs as a 3rd-party consumer (part 1)."""

# Protobuf
load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")

# Go rules and toolchain
load("@io_bazel_rules_go//go:deps.bzl", "go_register_toolchains", "go_rules_dependencies")
load("//bazel:go_deps.bzl", "go_dependencies")
load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies")

# CC toolchain
load("@com_grail_bazel_toolchain//toolchain:deps.bzl", "bazel_toolchain_dependencies")
load("@com_grail_bazel_toolchain//toolchain:rules.bzl", "llvm_toolchain")

# Python toolchain
load("@rules_python//python:repositories.bzl", "python_register_toolchains")

# Docker
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)
load("@io_bazel_rules_docker//repositories:deps.bzl", container_deps = "deps")
load(
    "@io_bazel_rules_docker//cc:image.bzl",
    _cc_image_repos = "repositories",
)
load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py_image_repos = "repositories",
)
load("@io_bazel_rules_docker//container:container.bzl", "container_pull")

# Googleapis
load("@com_google_googleapis//:repository_rules.bzl", "switched_rules_by_language")

# gRPC
load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")

# Bazel skylib
load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")

def intrinsic_sdks_deps_1(register_go_toolchain = True):
    """Loads workspace dependencies needed for the Intrinsic SDKs.

    This is one out of several non-optional parts. Please see intrinsic_sdks_deps_0() in
    intrinsic_sdks_deps_0.bzl for more details.

    Args:
        register_go_toolchain: if False, skips calling `go_register_toolchains`.
            This is useful if this function is called from a separate WORKSPACE
            that registers its own toolchain. `go_register_toolchains` is not
            hermetic and fails if a toolchain is already registered.
    """

    # Protobuf
    protobuf_deps()

    # Go rules and toolchain (first part)
    go_dependencies()

    go_rules_dependencies()

    if register_go_toolchain:
        go_register_toolchains(version = "1.19.5")

    # CC toolchain
    # How to upgrade:
    # - Pick a new version that runs on a stable OS similar enough to our sysroot from
    #   https://releases.llvm.org/download.html
    # - Documentation is in
    #   https://github.com/grailbio/bazel-toolchain/blob/master/toolchain/rules.bzl
    # - If system files are not found, add them in ../BUILD.sysroot
    bazel_toolchain_dependencies()
    llvm_toolchain(
        name = "llvm_toolchain",
        distribution = "clang+llvm-14.0.0-x86_64-linux-gnu-ubuntu-18.04.tar.xz",
        llvm_version = "14.0.0",
        sysroot = {
            "linux-x86_64": "@com_googleapis_storage_chrome_linux_amd64_sysroot//:all_files",
        },
    )

    # Python toolchain
    python_register_toolchains(
        name = "local_config_python",
        python_version = "3.11",
    )

    # Docker
    container_repositories()

    container_deps()

    _cc_image_repos()

    _py_image_repos()

    container_pull(
        name = "ubuntu",
        digest = "sha256:7c9c7fed23def3653a0da5bc9ecb651efe155ebd5802c7ba5d585edaa6c89496",
        registry = "index.docker.io",
        repository = "library/ubuntu:focal-20220113",
    )

    container_pull(
        name = "distroless_base_amd64",
        digest = "sha256:eaddb8ca70848a43fab351226d9549a571f68d9427c53356114fedd3711b5d73",
        registry = "gcr.io",
        repository = "distroless/base",
    )

    # Go rules and toolchain (second part)

    # Import Gazelle's dependencies and tell Gazelle where to look for '# gazelle:repository_macro'
    # or '# gazelle:repository' directives in gazelle_config.bzl (default is the main WORKSPACE
    # file, which could be the WORKSPACE file of another repository).
    # This needs to be the last invocation of gazelle_dependencies() for
    # 'go_repository_default_config' to have an effect (e.g., the Docker macros above call
    # gazelle_dependencies() internally).
    gazelle_dependencies(go_repository_default_config = Label("//:gazelle_config.bzl"))

    # Googleapis
    switched_rules_by_language(
        name = "com_google_googleapis_imports",
        cc = True,
        grpc = True,
        python = True,
        go = True,
    )

    # gRPC
    grpc_deps()

    # Bazel skylib
    bazel_skylib_workspace()
