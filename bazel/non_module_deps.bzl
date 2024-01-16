# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for non-module dependencies
"""

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive", "http_file", "http_jar")

def non_module_deps():
    """
    Declare repos here which have not been migrated to Bzlmod yet.
    """

    # Sysroot and libc
    # How to upgrade:
    # - Find image in https://storage.googleapis.com/chrome-linux-sysroot/ for amd64 for
    #   a stable Linux (here: Debian stretch), of this pick a current build.
    # - Verify the image contains expected /lib/x86_64-linux-gnu/libc* and defines correct
    #   __GLIBC_MINOR__ in /usr/include/features.h
    # - If system files are not found, add them in ../BUILD.sysroot
    http_archive(
        name = "com_googleapis_storage_chrome_linux_amd64_sysroot",
        build_file = Label("//intrinsic/production/external:BUILD.sysroot"),
        sha256 = "66bed6fb2617a50227a824b1f9cfaf0a031ce33e6635edaa2148f71a5d50be48",
        urls = [
            # features.h defines GLIBC 2.24. Contains /lib/x86_64-linux-gnu/libc-2.24.so,
            # last modified by Chrome 2018-02-22.
            "https://storage.googleapis.com/chrome-linux-sysroot/toolchain/15b7efb900d75f7316c6e713e80f87b9904791b1/debian_stretch_amd64_sysroot.tar.xz",
        ],
    )

    http_archive(
        name = "io_bazel_rules_docker",
        urls = [
            "https://github.com/bazelbuild/rules_docker/archive/ca2f3086ead9f751975d77db0255ffe9ee07a781.tar.gz",
        ],
        sha256 = "f6d71a193ff6df39900417b50e67a5cf0baad2e90f83c8aefe66902acce4c34d",
        strip_prefix = "rules_docker-ca2f3086ead9f751975d77db0255ffe9ee07a781",
    )
    http_archive(
        name = "com_google_googleapis",
        urls = [
            "https://github.com/googleapis/googleapis/archive/f3d6f41ed50ae9271fbf9ce2355d1f1e8afb4d94.zip",
        ],
        sha256 = "6c005ec1356d00821c00529b7d1283669633caf7e1e30d06909dda85a351b42f",
        strip_prefix = "googleapis-f3d6f41ed50ae9271fbf9ce2355d1f1e8afb4d94",
        patches = [
            Label("//intrinsic/production/external/patches:0004-Simplify-longrunning_py_proto.patch"),
        ],
        patch_args = [
            "-p1",
        ],
    )

    git_repository(
        name = "com_github_google_flatbuffers",
        remote = "https://github.com/google/flatbuffers.git",
        commit = "615616cb5549a34bdf288c04bc1b94bd7a65c396",
        shallow_since = "1644943722 -0500",
    )
    http_file(
        name = "go_puller_linux_amd64",
        executable = True,
        sha256 = "08b8963cce9234f57055bafc7cadd1624cdce3c5990048cea1df453d7d288bc6",
        urls = [
            "https://storage.googleapis.com/rules_docker/aad94363e63d31d574cf701df484b3e8b868a96a/puller-linux-amd64",
        ],
    )
    http_jar(
        name = "firestore_emulator",
        sha256 = "1f08a8f7133edf2e7b355db0da162654df2b0967610d3de2f12b8ce07c493f5f",
        urls = ["https://storage.googleapis.com/firebase-preview-drop/emulator/cloud-firestore-emulator-v1.18.2.jar"],
    )

def _non_module_deps_impl(ctx):  # @unused
    non_module_deps()

    # When included from WORKSPACE, we need repo_mapping for local_config_python
    git_repository(
        name = "pybind11_abseil",
        remote = "https://github.com/pybind/pybind11_abseil.git",
        commit = "2bf606ceddb0b7d874022defa8ea6d2d3e1605ad",
        shallow_since = "1684958620 -0700",
    )
    git_repository(
        name = "pybind11_protobuf",
        commit = "5baa2dc9d93e3b608cde86dfa4b8c63aeab4ac78",
        remote = "https://github.com/pybind/pybind11_protobuf.git",
        shallow_since = "1687199891 -0700",
    )

non_module_deps_ext = module_extension(implementation = _non_module_deps_impl)
