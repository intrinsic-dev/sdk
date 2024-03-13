# Copyright 2023 Intrinsic Innovation LLC

"""
Module extension for non-module dependencies
"""

load("@bazel_tools//tools/build_defs/repo:git.bzl", git_repository = "new_git_repository")
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

    http_archive(
        name = "com_google_fhir",
        url = "https://github.com/google/fhir/archive/f3128b9832ae0a8408587262226e870416f76faf.tar.gz",  # 2024-01-29
        strip_prefix = "fhir-f3128b9832ae0a8408587262226e870416f76faf",
        sha256 = "cbb2162ad280c558ca70c878aceb356e69024c5198a4020c0b4e8e4371619fb9",
    )

    http_archive(
        name = "com_google_cel_cpp",
        url = "https://github.com/google/cel-cpp/archive/037873163975964a80a188ad7f936cb4f37f0684.tar.gz",  # 2024-01-29
        strip_prefix = "cel-cpp-037873163975964a80a188ad7f936cb4f37f0684",
        sha256 = "d56e8c15b55240c92143ee3ed717956c67961a24f97711ca410030de92633288",
    )

    XLS_COMMIT = "507b33b5bdd696adb7933a6617b65c70e46d4703"  # 2024-03-06
    http_file(
        name = "com_google_xls_strong_int_h",
        downloaded_file_path = "strong_int.h",
        urls = ["https://raw.githubusercontent.com/google/xls/%s/xls/common/strong_int.h" % XLS_COMMIT],
        sha256 = "4daad402bc0913e05b83d0bded9dd699738935e6d59d1424c99c944d6e0c2897",
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
