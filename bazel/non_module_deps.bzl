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
            "https://github.com/googleapis/googleapis/archive/d9250048e9b9df4d8a0ce67b8ccf84e0aab0d50e.tar.gz",
        ],
        sha256 = "eaef89b65424505b2802ca13b6e0bdc5d302e0c477c78a4e41ecefbebed2c03e",
        strip_prefix = "googleapis-d9250048e9b9df4d8a0ce67b8ccf84e0aab0d50e",
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

    http_archive(
        name = "io_opentelemetry_cpp",
        urls = [
            "https://storage.googleapis.com/cloud-cpp-community-archive/io_opentelemetry_cpp/v1.13.0.tar.gz",
            "https://github.com/open-telemetry/opentelemetry-cpp/archive/v1.13.0.tar.gz",
        ],
        sha256 = "7735cc56507149686e6019e06f588317099d4522480be5f38a2a09ec69af1706",
        strip_prefix = "opentelemetry-cpp-1.13.0",
    )

    # Google Cloud Platform C++ Client Libraries
    http_archive(
        name = "google_cloud_cpp",
        strip_prefix = "google-cloud-cpp-2.20.0",
        sha256 = "9b2ad4500f911cfb159546becba303ce12073ab3975eb639f1101fc7ac2e5b08",
        urls = ["https://github.com/googleapis/google-cloud-cpp/archive/refs/tags/v2.20.0.zip"],
    )

    http_archive(
        name = "com_google_nisaba",
        url = "https://github.com/google-research/nisaba/archive/0dea3665cb64a3c66c080700ee5f1748900971fb.tar.gz",  # 2024-01-25
        strip_prefix = "nisaba-0dea3665cb64a3c66c080700ee5f1748900971fb",
        sha256 = "e589e0690cf53fc9dde92a4b6a6309147d1fecdc0c72285ac09806739d3dded3",
    )

    # OpenCV
    http_archive(
        name = "opencv",
        build_file = Label("//intrinsic/production/external:BUILD.opencv"),
        sha256 = "9b5b64d50bf4a3ddeab430a9b13c5f9e023c9e67639ab50a74d0c298b5a61b74",
        strip_prefix = "opencv-4.9.0",
        urls = [
            "https://github.com/opencv/opencv/archive/4.9.0.zip",
        ],
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
