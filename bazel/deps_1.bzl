# Copyright 2023 Intrinsic Innovation LLC

"""Workspace dependencies needed for the Intrinsic SDKs as a 3rd-party consumer (part 1)."""

load("@aspect_bazel_lib//lib:repositories.bzl", "aspect_bazel_lib_dependencies", "aspect_bazel_lib_register_toolchains")
load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies")
load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")
load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")
load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")
load("@io_bazel_rules_go//go:deps.bzl", "go_register_toolchains", "go_rules_dependencies")
load("@rules_foreign_cc//foreign_cc:repositories.bzl", "rules_foreign_cc_dependencies")
load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")
load("@toolchains_llvm//toolchain:deps.bzl", "bazel_toolchain_dependencies")
load("@toolchains_llvm//toolchain:rules.bzl", "llvm_toolchain")
load("//bazel:extension_for_com_google_googleapis.bzl", "extension_for_com_google_googleapis")
load("//bazel:go_deps.bzl", "go_dependencies")

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
        go_register_toolchains(version = "1.22.1")

    # CC toolchain
    # How to upgrade:
    # - Pick a new version that runs on a stable OS similar enough to our sysroot from
    #   https://releases.llvm.org/download.html
    # - Documentation is in
    #   https://github.com/bazel-contrib/toolchains_llvm/blob/master/toolchain/rules.bzl
    # - If system files are not found, add them in ../BUILD.sysroot
    # - BUG(b/334809653): You might need to manually fix the mirror.
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
    py_repositories()

    # Required bazel-lib dependencies
    aspect_bazel_lib_dependencies()

    # Register bazel-lib toolchains
    aspect_bazel_lib_register_toolchains()

    # Go rules and toolchain (second part)

    # Import Gazelle's dependencies and tell Gazelle where to look for '# gazelle:repository_macro'
    # or '# gazelle:repository' directives in gazelle_config.bzl (default is the main WORKSPACE
    # file, which could be the WORKSPACE file of another repository).
    # This needs to be the last invocation of gazelle_dependencies() for
    # 'go_repository_default_config' to have an effect (e.g., the Docker macros above call
    # gazelle_dependencies() internally).
    gazelle_dependencies(go_repository_default_config = Label("//:gazelle_config.bzl"))

    # Googleapis
    extension_for_com_google_googleapis()

    # gRPC
    grpc_deps()

    # Bazel skylib
    bazel_skylib_workspace()

    # Rules Foreign CC
    rules_foreign_cc_dependencies()
